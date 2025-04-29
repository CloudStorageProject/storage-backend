from pydantic import BaseModel


class SubscriptionView(BaseModel):
    name: str
    space: float
    price: float
    description: str

    class Config:
        from_attributes = True


class SubscriptionInfo(BaseModel):
    name: str


class SessionIdentifier(BaseModel):
    id: str

    class Config:
        from_attributes = True


class WebhookResponse(BaseModel):
    status: str