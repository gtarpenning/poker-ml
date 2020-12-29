from itertools import combinations as comb
from collections import defaultdict, Counter
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
    cards_s = sorted([utils.c_lookup[x[0]] for x in cards], reverse=True)
    for card, num in counts.items():
        if num == 4:  # 4 of a kind!
            high = cards_s[0]
            if high == utils.c_lookup[card]:
                high = cards_s[4]
            return 105 + utils.c_lookup[card] + high / 15
        elif num == 3:
            big += [card]
        elif num == 2:
            small += [card]

    if len(big) == 2:  # full house with two triples
        if utils.c_lookup[big[0]] > utils.c_lookup[big[1]]:
            return 90 + utils.c_lookup[big[0]] + utils.c_lookup[big[1]] / 15
        else:
            return 90 + utils.c_lookup[big[1]] + utils.c_lookup[big[0]] / 15

    if len(big) == 1 and len(small) >= 1:  # Full house 3 + 2
        return 90 + utils.c_lookup[big[0]] + max([utils.c_lookup[x[0]] for x in small]) / 15

    # Flush:
    for suit, count in suit_counts.items():
        if count >= 5:  # FLUSH
            flush_cards = sorted([utils.c_lookup[x[0]] for x in cards if x[1] == suit], reverse=True)[:5]
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
        high = sorted([utils.c_lookup[x[0]] for x in cards if x not in big], reverse=True)
        return 45 + utils.c_lookup[big[0]] + (high[0] / 15) + (high[1] / (15**2))

    if len(small) >= 2:  # 2 pair
        top = max([utils.c_lookup[x[0]] for x in small])
        bottom = max([utils.c_lookup[x[0]] for x in small if utils.c_lookup[x[0]] != top])
        high = max([utils.c_lookup[x[0]] for x in cards if x not in small])
        return 30 + top + (bottom / 15) + (high / (15**2))

    if len(small) == 1:
        high = sorted([utils.c_lookup[x[0]] for x in cards if x not in small], reverse=True)
        return 15 + utils.c_lookup[small[0]] + get_single_card_scores(high, 3)

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
    possible_hole_cards = [x for x in comb(deck, 2)]
    print("Number of poker hole card possibilities (52 C 2):", len(possible_hole_cards))
    hole_combos = make_hole_card_combo_dict(possible_hole_cards)
    print("Number of unique hole card combos:", len(hole_combos))
    # all_boards = [x for x in permutations(deck, 5)]
    # print("Number of unique 5 card boards:", len(all_boards))  # 311,875,200
    unique_boards = [x for x in comb(deck, 5)]
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


def get_known_board_equity(hand, b):
    start = datetime.now()
    deck = utils.make_deck()
    deck = [x for x in deck if x not in hand + b]

    hero_scores = [get_score(x + b + hand) for x in comb(deck, 2)]
    median = np.median(hero_scores)

    all_scores = [get_score(h + b + x) for h in comb(deck, 2) for x in comb(deck, 2) if h[0] not in x and h[1] not in x]
    wins = 0
    for score, count in Counter(all_scores).items():
        if median > score:
            wins += count
        elif median == score:
            wins += count / 2

    print(f"Took: {(datetime.now() - start).seconds} to determine GTO equity")
    return wins / len(all_scores)


def main():
    times = []
    for i in range(1000):
        deck = utils.make_deck()
        hand = deck[:7]
        start = datetime.now()
        s = get_score(hand)
        times += [(datetime.now() - start).microseconds]

    print("Average get_sum v2", sum(times) / len(times))


if __name__ == '__main__':
    main()
