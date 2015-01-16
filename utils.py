from deuces.card import Card
from deuces.evaluator import Evaluator

class HandRank:
    def evaluate_hand(self,board,hand):
        dueces_board = [Card.new(board[0]),Card.new(board[1]),Card.new(board[2]),Card.new(board[3]),Card.new(board[4])]
        dueces_hand = [Card.new(hand[0]),Card.new(hand[1])]
        evaluator = Evaluator()
        score = evaluator.evaluate(dueces_board, dueces_hand)
        hand_rank = evaluator.get_rank_class(score)
        hand_rank_str = evaluator.class_to_string(hand_rank)
        return (hand_rank_str,score)