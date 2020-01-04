class AppException(Exception):
    """ Some exception """


class RecordNotFound(AppException):
    """ Requested record in database was not found """


class BadRequest(AppException):
    """ Bad request """


class BadRequest_Important(Exception):
    """ Bad request supposed to log """
