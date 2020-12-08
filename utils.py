
SUITS = ['h', 's', 'd', 'c']
CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
DECK = [c + s for c in CARDS for s in SUITS]


def get_hand_dict_from_combos(combo_data):
    return_dict = {}

    for (cards, val) in combo_data:
        if len(cards) == 3 or cards[0] == cards[1]:
            for suit1 in SUITS:
                for suit2 in SUITS:
                    if suit1 != suit2:
                        return_dict[(cards[0] + suit1, cards[1] + suit2)] = val
        else:
            for suit in SUITS:
                return_dict[(cards[0] + suit, cards[1] + suit)] = val

    return return_dict
