from itertools import combinations as comb
from collections import Counter
from tqdm import tqdm
import json
import os
from datetime import datetime
import numpy as np
# local imports
import compute
import utils


def get_scores_for_holecards():
    deck, possible_hole_cards, hole_combos, card_lookup = compute.setup()  # , all_boards
    data = {}

    deck = utils.make_deck()
    for str_hand in tqdm(card_lookup):
        if str_hand in data:
            print(f"skipping {str_hand}")
            continue

        data[str_hand] = []
        hand = card_lookup[str_hand][0]
        deck.remove(hand[0])
        deck.remove(hand[1])
        data[str_hand] = [compute.get_score(bd + hand) for bd in comb(deck, 5)]

        deck += [hand[0], hand[1]]

    with open("./brain_lookups/hole_card_boards.json", "w") as jsonFile:
        json.dump(data, jsonFile)


def make_hole_card_percentages():
    deck, possible_hole_cards, hole_combos, card_lookup = compute.setup()
    hole_data = None
    start = datetime.now()
    with open("./brain_lookups/hole_card_boards.json", "r") as jsonFile:
        hole_data = json.load(jsonFile)

    print("took:", (datetime.now() - start).seconds, "seconds to load json.")

    start = datetime.now()
    all_hand_board_scores = sorted([j for x in hole_data for j in hole_data[x]], reverse=True)
    total_scores_len = len(all_hand_board_scores)

    print(all_hand_board_scores[-100:])

    winning_score_dict = {}
    for i in range(2, 10):
        winning_index = int(total_scores_len / i) - 1
        winning_score_dict[str(i)] = all_hand_board_scores[winning_index]

    print("took:", (datetime.now() - start).seconds, "seconds to sort scores.")
    print(winning_score_dict)
    del all_hand_board_scores

    hole_card_percentages = {}
    # for str_hand in tqdm(card_lookup):
    str_hand = 'AA'
    print("hand:", str_hand)
    print(Counter(hole_data[str_hand]))
    num_wins = {key: 0 for key in winning_score_dict.keys()}
    for score in hole_data[str_hand]:
        for num_players, winning_score in winning_score_dict.items():
            if score > winning_score:
                num_wins[num_players] += 1
            elif score == winning_score:
                num_wins[num_players] += 0.5

    num_wins = {key: val / len(hole_data['22']) for key, val in num_wins.items()}
    print(num_wins)
    for real_hand in card_lookup[str_hand]:
        hole_card_percentages[real_hand] = num_wins

    with open("./brain_lookups/hole_card_percentages.json", "w") as jsonFile:
        json.dump(hole_data, jsonFile)


# get_scores_for_holecards()
make_hole_card_percentages()




"""
2 handed game, look to average hand score to determine winning %
3 handed game, to win, need other two lower. thus to win we need to be on ave
    in the top 1/3 of ALL hands, not just our current hand



"""
