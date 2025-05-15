from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import get_full_auth, get_basic_auth
from app.payments.schemas import (
    SubscriptionInfo, SessionIdentifier, WebhookResponse,
    SubscriptionView
)
from app.auth.schemas import CurrentUser
from app.payments.services import (
    create_subscription, handle_webhook, get_all_subscription_types
)
from app.payments.errors import (
    AlreadySubscribed, NonExistentSubscription, WebhookSignatureError,
    InvalidWebhookPayload, CannotSetDefaultStatus, CouldNotCreateCustomer
)


payment_router = APIRouter()


@payment_router.get("/overview")
def subscriptions_overview(
    current_user: CurrentUser = Depends(get_basic_auth),
    db: Session = Depends(get_db)) -> list[SubscriptionView]:
    return get_all_subscription_types(db)


@payment_router.post("/subscribe")
def subscribe(
    sub_info: SubscriptionInfo, 
    current_user: CurrentUser = Depends(get_full_auth),
    db: Session = Depends(get_db)) -> SessionIdentifier:
    try:
        return create_subscription(db, current_user, sub_info)
    except NonExistentSubscription as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (AlreadySubscribed, CannotSetDefaultStatus)  as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CouldNotCreateCustomer as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    

@payment_router.post("/webhook")
async def webhook(
    request: Request,
    db: Session = Depends(get_db)) -> WebhookResponse:
    try:
        return await handle_webhook(request, db)
    except (InvalidWebhookPayload, WebhookSignatureError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
