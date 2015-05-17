
class PangaeaDealerErrorCodes():
    NA = 0
    InvalidArgumentError = 200
    NotFoundError = 201,
    AlreadyExists = 202,
    BettingError = 203,
    ServerError = 299


class PangeaException(Exception):
    def __init__(self, error_code, error_message):
        super().__init__(error_message)
        self.error_code = error_code

    @staticmethod
    def missing_field(field_name):
        raise PangeaException(PangaeaDealerErrorCodes.InvalidArgumentError, "Missing field: {0}".format(field_name))