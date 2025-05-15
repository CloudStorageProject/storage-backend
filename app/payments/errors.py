class AlreadySubscribed(Exception):
    pass

class NonExistentSubscription(Exception):
    pass

class InvalidWebhookPayload(Exception):
    pass

class WebhookSignatureError(Exception):
    pass

class CannotSetDefaultStatus(Exception):
    pass

class CouldNotCreateCustomer(Exception):
    pass