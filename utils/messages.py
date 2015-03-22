import json
import datetime
import utils
from utils.errors import PangaeaDealerErrorCodes
from utils import PangeaJsonEncoder


class PangeaMessage(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    @staticmethod
    def from_json(msg):
        data = json.loads(msg)
        return PangeaMessage(**data)

    def to_json(self):
        return json.dumps(self.__dict__, cls=PangeaJsonEncoder)

    def __str__(self):
        return self.to_json()

    def __getattr__(self, item):
        # Return None rather then throwing an AttributeError exception
        return None

    @staticmethod
    def from_exception(message_type, ex: Exception):
        error_code = ex.error_code if hasattr(ex, "error_code") else PangaeaDealerErrorCodes.ServerError

        return PangeaMessage(message_type=str(message_type),
                             error_code=error_code,
                             error_message=str(ex))