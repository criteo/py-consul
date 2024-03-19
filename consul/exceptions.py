class ConsulException(Exception):
    pass


class ACLDisabled(ConsulException):
    pass


class ACLPermissionDenied(ConsulException):
    pass


class NotFound(ConsulException):
    pass


class Timeout(ConsulException):
    pass


class BadRequest(ConsulException):
    pass


class ClientError(ConsulException):
    """Encapsulates 4xx Http error code"""
