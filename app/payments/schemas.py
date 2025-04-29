from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    name: str


class SessionIdentifier(BaseModel):
    id: str

    class Config:
        from_attributes = True


class WebhookResponse(BaseModel):
    status: str