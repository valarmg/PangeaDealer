from enum import Enum


class PangaeaDealerErrorCodes(Enum):
    NA = 0
    InvalidArgumentError = 200
    NotFoundError = 201,
    AlreadyExists = 202,
    ServerError = 299


class PangeaException(Exception):
    def __init__(self, error_code: PangaeaDealerErrorCodes, error_message):
        super().__init__(error_message)
        self.error_code = error_code

    @staticmethod
    def missing_field(field_name):
        raise PangeaException(PangaeaDealerErrorCodes.InvalidArgumentError, "Missing field: {0}".format(field_name))