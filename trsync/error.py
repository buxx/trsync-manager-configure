class AuthenticationError(Exception):
    pass


class CommunicationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class FailToSetPassword(Exception):
    pass


class FailToGetPassword(Exception):
    pass
