from loguru import logger
from app.models import SubscriptionType
from sqlalchemy import func, select, update, delete
from app.auth.schemas import CurrentUser
from sqlalchemy.orm import Session
from app.models import User, Subscription
from app.main import settings
from app.payments.schemas import SessionIdentifier
from app.payments.errors import (
    InvalidWebhookPayload, WebhookSignatureError, CouldNotCreateCustomer
)
from datetime import datetime, timedelta
from app.database import get_db
import stripe
import schedule
import time
import threading


stripe.api_key = settings.STRIPE_SECRET_KEY


def remove_expired_subscriptions():
    db = next(get_db())
    now = datetime.utcnow()

    logger.debug(f"{now}, trying to remove expired subscriptions...")

    subquery = select(Subscription.user_id).filter(Subscription.subscription_end_date < now).subquery()

    db.execute(
        update(User)
        .where(User.id.in_(select(subquery)))
        .values(subscription_type_id=1)
    )

    db.execute(
        delete(Subscription)
        .where(Subscription.subscription_end_date < now)
    )

    db.commit()
    db.close()


def periodic_task():
    schedule.every(1).minutes.do(remove_expired_subscriptions)
    while True:
        schedule.run_pending()
        time.sleep(1)


def initiate_subscription_task():
    logger.debug("Starting a thread to monitor expired subscriptions...")
    task_thread = threading.Thread(target=periodic_task)
    task_thread.daemon = True
    task_thread.start()


def handle_successful_payment(event, db: Session) -> None:
    invoice = event['data']['object']
    stripe_customer_id = invoice['customer']
    stripe_subscription_id = invoice['parent']['subscription_details']['subscription']
    stripe_price_id = invoice['lines']['data'][0]['pricing']['price_details']['price']

    user = db.query(User).filter_by(stripe_customer_id=stripe_customer_id).first()
    subscription_type = db.query(SubscriptionType).filter_by(stripe_price_id=stripe_price_id).first()
    subscription = db.query(Subscription).filter_by(user_id=user.id).first()

    now = datetime.utcnow()

    if subscription:
        base_date = subscription.subscription_end_date
        subscription.subscription_end_date = base_date + timedelta(days=32)
        logger.debug(f"Prolonged subscription of user {user.username} to {subscription.subscription_end_date}")
    else:
        end_date = now + timedelta(days=32)

        new_subscription = Subscription(
            subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            subscription_start_date=now,
            subscription_end_date=end_date,
            user_id=user.id,
            subscription_type_id=subscription_type.id
        )

        db.add(new_subscription)

        logger.debug(f"Added new subscription '{subscription_type.name}' for {user.username} until {end_date}")
    
    user.subscription_type_id = subscription_type.id

    db.commit()


def try_construct_event(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        raise InvalidWebhookPayload("Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise WebhookSignatureError("Invalid signature")
    
    return event


def create_subscription_session(customer_id: str, price_id: str) -> SessionIdentifier:
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        customer=customer_id,
        success_url=settings.PAYMENT_SUCCESS_URL,
        cancel_url=settings.PAYMENT_FAILURE_URL
    )

    return SessionIdentifier(id=session.id)


def update_customer_id(db: Session, user_id: int, customer_id: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    user.stripe_customer_id = customer_id
    db.flush()


def create_stripe_customer(user: CurrentUser) -> str:
    try:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={
                "user_id": str(user.id)
            }
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise CouldNotCreateCustomer("Could not create a customer instance for you. Try again later.")


def init_subscription_types(session: Session) -> None:
    if session.query(func.count(SubscriptionType.id)).scalar() == 0:
        default_types = [
            SubscriptionType(name="User", space=5.0, price=0.0, description="", stripe_price_id="")
        ]

        prices = stripe.Price.list(active=True, expand=["data.product"])

        for price in prices:
            default_types.append(
                SubscriptionType(
                    name=price['product']['metadata']['name'],
                    space=price['product']['metadata']['space'],
                    price=price['unit_amount'] / 100.0,
                    description=price['product']['description'],
                    stripe_price_id=price['id']
                )
            )

        session.add_all(default_types)
        session.commit()
        logger.debug("Default subscription types added successfully!")