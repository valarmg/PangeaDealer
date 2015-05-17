from random import shuffle
import logging
from services import PangeaDbServiceBase
from models import Round
import operator
from models import Table
from modules.dealer import DealerModule
from modules.bet import BetModule


class DealerService(PangeaDbServiceBase):
    log = logging.getLogger(__name__)

    def __init__(self, db):
        super().__init__(db)
        self.dealer_module = DealerModule(db)
        self.bet_module = BetModule(db)
