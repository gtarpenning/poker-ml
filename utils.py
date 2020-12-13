
SUITS = ['h', 's', 'd', 'c']
CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
DECK = [c + s for c in CARDS for s in SUITS]

c_lookup = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, 'T': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}


def make_deck():
    return DECK


def get_hand_dict_from_combos(combo_data):
    return_dict = {}

    for (cards, val) in combo_data.items():
        if len(cards) == 3 or cards[0] == cards[1]:
            for suit1 in SUITS:
                for suit2 in SUITS:
                    if suit1 != suit2:
                        return_dict[(cards[0] + suit1, cards[1] + suit2)] = val
        else:
            for suit in SUITS:
                return_dict[(cards[0] + suit, cards[1] + suit)] = val

    return return_dict


def get_combos_from_hand_dict(hand_data):
    combos = {}
    for (card1, card2) in hand_data.keys():
        name = f"{card1[0]}{card2[0]}"
        if combos.get(f"{card2[0]}{card1[0]}"):
            name = f"{card2[0]}{card1[0]}"

        if card1[-1] != card2[-1] and card1[0] != card2[0]:  # off suited
            name += 'o'

        if not combos.get(name):
            combos[name] = []

        combos[name] += [hand_data[(card1, card2)]]
    return combos
