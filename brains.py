import json

import utils


class Brain():

    def __init__(self):
        pass

    def get_name(self):
        return self.__class__.__name__


class GTOBrain(Brain):

    def __init__(self):
        hole_data = json.load(open('hole_card_winning_percentages.json'))
        flop_data = json.load(open('flop_winning_percentages.json'))
        turn_data = json.load(open('turn_winning_percentages.json'))
        river_data = json.load(open('river_winning_percentages.json'))
        self.hole_cards = utils.get_hand_dict_from_combos(hole_data)
        self.flop_percentages = utils.get_hand_dict_from_combos(flop_data)
        self.turn_percentages = utils.get_hand_dict_from_combos(turn_data)
        self.river_percentages = utils.get_hand_dict_from_combos(river_data)

    def get_equity(self, hand, board):
        hand_scores = []
        if len(board) == 0:    # Hole Cards.
            hand_scores = self.hole_hands[self.hand]
        elif len(board) == 3:  # Flop
            hand_scores = self.flop_hands[(self.hand, board)]
        elif len(board) == 4:  # Turn
            hand_scores = self.turn_hands[(self.hand, board)]
        else:                        # River
            hand_scores = self.river_hands[(self.hand, board)]
