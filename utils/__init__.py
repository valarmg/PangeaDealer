from deuces.card import Card
from deuces.evaluator import Evaluator
from json import JSONEncoder
from bson import ObjectId


class PangeaJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()

        return JSONEncoder.default(self, obj)


class HandRank:
    @staticmethod
    def evaluate_hand(board, hand):
        if board is None or len(board) < 3:
            raise ValueError("Missing board cards")
        if hand is None or len(hand) < 2:
            raise ValueError("Missing hole cards")

        deuces_board = [Card.new(board[0]), Card.new(board[1]), Card.new(board[2]),
                        Card.new(board[3]), Card.new(board[4])]
        deuces_hand = [Card.new(hand[0]), Card.new(hand[1])]

        evaluator = Evaluator()
        score = evaluator.evaluate(deuces_board, deuces_hand)
        hand_rank = evaluator.get_rank_class(score)
        hand_rank_str = evaluator.class_to_string(hand_rank)

        return hand_rank_str, score