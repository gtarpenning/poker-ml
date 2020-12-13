from itertools import combinations, permutations
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime
import json
import os
import numpy as np

import utils


def make_hole_card_combo_dict(possible_hole_cards):
    hole_combos = {}
    for (card1, card2) in possible_hole_cards:
        name = f"{card1[0]}{card2[0]}"
        if hole_combos.get(f"{card2[0]}{card1[0]}"):
            name = f"{card2[0]}{card1[0]}"

        if card1[-1] != card2[-1] and card1[0] != card2[0]:  # off suited
            name += 'o'

        if not hole_combos.get(name):
            hole_combos[name] = 0

        hole_combos[name] += 1

    return hole_combos


c_lookup = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, 'T': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}


def get_single_card_scores(cards, num):
    return sum([x / (15**(i + 1)) for i, x in enumerate(cards[:num])])


def get_score(cards):
    counts = defaultdict(int)
    for card in cards:
        counts[card[0]] += 1

    suit_counts = defaultdict(int)
    for card in cards:
        suit_counts[card[1]] += 1

    big = []
    small = []
    cards_s = sorted([c_lookup[x[0]] for x in cards], reverse=True)
    for card, num in counts.items():
        if num == 4:  # 4 of a kind!
            high = cards_s[0]
            if high == c_lookup[card]:
                high = cards_s[4]
            return 105 + c_lookup[card] + high / 15
        elif num == 3:
            big += [card]
        elif num == 2:
            small += [card]

    if len(big) == 2:  # full house with two triples
        if c_lookup[big[0]] > c_lookup[big[1]]:
            return 90 + c_lookup[big[0]] + c_lookup[big[1]] / 15
        else:
            return 90 + c_lookup[big[1]] + c_lookup[big[0]] / 15

    if len(big) == 1 and len(small) >= 1:  # Full house 3 + 2
        return 90 + c_lookup[big[0]] + max([c_lookup[x[0]] for x in small]) / 15

    # Flush:
    for suit, count in suit_counts.items():
        if count >= 5:  # FLUSH
            flush_cards = sorted([c_lookup[x[0]] for x in cards if x[1] == suit], reverse=True)[:5]
            straight_counter = 0
            last_num = cards_s[0]
            for num in cards_s[1:]:
                if num == last_num - 1:
                    straight_counter += 1
                if straight_counter == 4 or (straight_counter == 3 and num == 2 and cards_s[0] == 14):
                    # Straight Flush lol
                    return 120 + get_single_card_scores(flush_cards, 5)
                last_num = num

            return 75 + get_single_card_scores(flush_cards, 5)

    # Straight
    straight_counter = 0
    last_num = cards_s[0]
    for num in cards_s[1:]:
        if num == last_num - 1:
            straight_counter += 1

        if straight_counter == 4 or (straight_counter == 3 and num == 2 and cards_s[0] == 14):
            return 60 + (num + 4)

        if num != last_num - 1 and num != last_num:
            straight_counter = 0

        last_num = num

    # Three of a kind
    if len(big) == 1 and len(small) == 0:
        high = sorted([c_lookup[x[0]] for x in cards if x not in big], reverse=True)
        return 45 + c_lookup[big[0]] + (high[0] / 15) + (high[1] / (15**2))

    if len(small) >= 2:  # 2 pair
        top = max([c_lookup[x[0]] for x in small])
        bottom = max([c_lookup[x[0]] for x in small if c_lookup[x[0]] != top])
        high = max([c_lookup[x[0]] for x in cards if x not in small])
        return 30 + top + (bottom / 15) + (high / (15**2))

    if len(small) == 1:
        high = sorted([c_lookup[x[0]] for x in cards if x not in small], reverse=True)
        return 15 + c_lookup[small[0]] + get_single_card_scores(high, 3)

    return get_single_card_scores(cards_s, 5)


def do_tests():
    tests = [
        # ('Ah', 'Ks', 'Qc', 'Jh', 'Th', '2c', '2s'),  # Straight
        # ('Ah', 'Kh', 'Qc', 'Jh', 'Th', '2h', '2s'),  # Flush
        # ('Ah', 'As', 'Kc', 'Jh', 'Th', 'Ks', '2s'),  # 2 Pair
        # ('Ah', 'Ks', '9c', 'Jh', 'Th', '2c', '4d'),  # High card
        # ('Ah', 'As', 'Ac', 'Jh', 'Th', '2c', '2s'),  # Full House
        # ('Ah', 'Ks', 'Qh', 'Jh', '2h', '2c', '2s'),  # 3 of a kind
        # ('Kh', 'Ks', 'Kc', 'Jh', '2h', '2c', '2s'),  # 3, 3 full house
        ('2h', '2s', '2c', '2d', 'Qh', 'Tc', '3s'),  # 4 of a kind
        ('2h', '2s', '2c', '2d', 'Ah', 'As', '3s'),  # 4-kind tie
        ('2h', '2s', '2c', '2d', 'Kh', 'Ks', '3s')
    ]
    for test in tests:
        print(get_score(test))


def get_card_lookup(possible_hole_cards, hole_combos):
    lookup = defaultdict(list)
    for (card1, card2) in possible_hole_cards:
        name = f"{card1[0]}{card2[0]}"
        if hole_combos.get(f"{card2[0]}{card1[0]}"):
            name = f"{card2[0]}{card1[0]}"

        if card1[-1] != card2[-1] and card1[0] != card2[0]:  # off suited
            name += 'o'

        lookup[name] += [(card1, card2)]
    return lookup


def setup():
    deck = utils.make_deck()
    possible_hole_cards = [x for x in combinations(deck, 2)]
    print("Number of poker hole card possibilities (52 C 2):", len(possible_hole_cards))
    hole_combos = make_hole_card_combo_dict(possible_hole_cards)
    print("Number of unique hole card combos:", len(hole_combos))
    # all_boards = [x for x in permutations(deck, 5)]
    # print("Number of unique 5 card boards:", len(all_boards))  # 311,875,200
    unique_boards = [x for x in combinations(deck, 5)]
    print("Number of unique 5 card boards:", len(unique_boards))
    card_lookup = get_card_lookup(possible_hole_cards, hole_combos)

    return deck, possible_hole_cards, hole_combos, card_lookup  # , all_boards


def is_flush_possible(cards):
    suit_counts = defaultdict(int)
    for card in cards:
        suit_counts[card[1]] += 1

    for suit, count in suit_counts.items():
        if count >= 3:
            return True


def get_scores_for_holecards():
    deck, possible_hole_cards, hole_combos = setup()  # , all_boards

    if 'hole_card_medians.json' in os.listdir():
        with open("hole_card_medians.json", "r") as jsonFile:
            data = json.load(jsonFile)
    else:
        data = {}

    for str_hand in tqdm(hole_combos.keys()):
        if str_hand in data:
            # print("Skipping hand:", str_hand)
            continue

        hands_dict = utils.get_hand_dict_from_combos({str_hand: None})
        real_hands = [x for x in hands_dict.keys()]
        hand = real_hands[0]

        deck.remove(hand[0])
        deck.remove(hand[1])

        board_combos = [x for x in combinations(deck, 5)]

        cum_score = []
        for board in board_combos:
            cum_score += [get_score(hand + board)]

        deck += [hand[0], hand[1]]
        score = round(np.median(cum_score), 4)
        data[str_hand] = score

        print("Ave hand score for hand:", str_hand, "->", score)
        with open("hole_card_medians.json", "w") as jsonFile:
            json.dump(data, jsonFile)

    return data


def get_hand_strength_order(data):
    return sorted(data.items(), key=lambda x: x[1], reverse=True)


def calculate_hole_card_win_percentage(ave_hand_score, hole_combos):
    out_data = defaultdict(int)
    total = sum([x[1] for x in hole_combos.items()])
    for (hand1, score1) in ave_hand_score:
        for (hand2, score2) in ave_hand_score:
            if hand1 != hand2 and score1 > score2:
                out_data[hand1] += (hole_combos[hand2])

        out_data[hand1] /= total

    return out_data


def get_unique_score_lookup():
    deck = utils.make_deck()
    board_combos = [x for x in combinations(deck, 5)]

    scores = defaultdict(int)
    for board in board_combos:
        score = get_score(board)
        scores[score] += 1

    print("num unique scores:", len(set(scores.keys())))
    lookup = {}
    """
    {
        1-2878: frequency of score
    }

    """
    for i, val in enumerate(sorted(list(scores.keys()))):
        lookup[i] = scores[val]

    return lookup


def main():
    # do_tests()
    # data = get_scores_for_holecards()
    # print("Hand strength order.")
    # order = get_hand_strength_order(data)
    # for hand in order:
    # print(hand[0], hand[1])
    # _, _, hole_combos = setup()
    # hand_wins = calculate_hole_card_win_percentage(order, hole_combos)
    # with open('hole_card_winning_percentages_median.json', 'w') as f:
    #     json.dump(hand_wins, f)
    d = get_unique_score_lookup()
    percents = defaultdict(int)
    for score1 in d:
        for score2 in d:
            if score1 > score2:
                percents[score1] += d[score2] / 2598960

    print(percents)


if __name__ == '__main__':
    main()
