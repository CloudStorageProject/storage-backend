from fastapi import Request
from sqlalchemy.orm import Session
from app.models import SubscriptionType
from app.payments.errors import (
    AlreadySubscribed, NonExistentSubscription, CannotSetDefaultStatus
)
from app.auth.schemas import CurrentUser
from app.payments.schemas import (
    SubscriptionInfo, SessionIdentifier, WebhookResponse,
    SubscriptionView
)
from app.payments.utils import (
    create_stripe_customer, update_customer_id, create_subscription_session,
    try_construct_event, handle_successful_payment
)


def get_all_subscription_types(db: Session) -> list[SubscriptionView]:
    return db.query(SubscriptionType).filter(SubscriptionType.name != "User").all()


def create_subscription(db: Session, current_user: CurrentUser, sub_info: SubscriptionInfo) -> SessionIdentifier:
    subscription_type = db.query(SubscriptionType).filter(SubscriptionType.name == sub_info.name).first()

    if sub_info.name == "User":
        raise CannotSetDefaultStatus("You can't buy this status.")

    if not subscription_type:
        raise NonExistentSubscription("This subscription type does not exist.")
    
    if current_user.subscription_name != "User":
        raise AlreadySubscribed("You are already subscribed.")
    
    if current_user.customer_id == "":
        customer_id = create_stripe_customer(current_user)

        update_customer_id(db, current_user.id, customer_id)
        db.commit()

        current_user.customer_id = customer_id

    return create_subscription_session(current_user.customer_id, subscription_type.stripe_price_id)


async def handle_webhook(request: Request, db: Session) -> WebhookResponse:
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    event = try_construct_event(payload, sig_header)

    if event['type'] == 'invoice.payment_succeeded':
        handle_successful_payment(event, db)
    
    return WebhookResponse(status="success")

    