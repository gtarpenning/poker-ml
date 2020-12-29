from collections import defaultdict
from tqdm import tqdm
import random
import json
# local
import utils
from compute import get_score


ROUNDS = 100000000 # 1 million
EPOCHS = 1
NUM_PLAYERS = 2


def get_combos_from_hand_dict(hand_data):
    combos = {}
    for ((card1, card2), board) in hand_data.keys():
        name = f"{card1[0]}{card2[0]}"
        if combos.get(f"{card2[0]}{card1[0]}"):
            name = f"{card2[0]}{card1[0]}"

        if card1[-1] != card2[-1] and card1[0] != card2[0]:  # off suited
            name += 'o'

        if not combos.get((name, board)):
            combos[(name, board)] = []

        combos[(name, board)] += [hand_data[((card1, card2), board)]]
    return combos


def shuffle_and_draw(num_cards):
    deck = utils.make_deck().copy()
    random.shuffle(deck)
    board = tuple(deck[:num_cards])
    deck = deck[num_cards:]

    return deck, board


all_holecard_percentages = defaultdict(dict)
for num_players in range(2, NUM_PLAYERS + 1):
    hand_wins = defaultdict(int)
    hand_plays = defaultdict(int)
    for _ in range(EPOCHS):
        for _ in tqdm(range(ROUNDS)):
            deck, board = shuffle_and_draw(5)
            hands = []

            for i in range(num_players):
                h = tuple(deck[i * 2: (i + 1) * 2])
                if utils.c_lookup[h[0][0]] < utils.c_lookup[h[1][0]]:
                    h = (h[1], h[0])
                elif h[0][0] == h[1][0] and h[0][1] < h[1][1]:
                    h = (h[1], h[0])

                hands += [(h, get_score(h + board))]
                hand_plays[(h, board)] += 1

            winner_hands = sorted(hands, key=lambda x: x[1], reverse=True)
            if winner_hands[0][1] > winner_hands[1][1]:  # Clear winner
                hand_wins[(winner_hands[0][0], board)] += 1
            else:  # ties
                winning_val = winner_hands[0][1]
                for hand in winner_hands:
                    if hand[1] == winning_val:
                        hand_wins[(hand[0], board)] += 0.5
                    else:
                        break

        hand_win_percents = {key: val / hand_plays[key] for key, val in hand_wins.items()}
        # average over hands of similar type
        combos = get_combos_from_hand_dict(hand_win_percents)
        adj_percent = {key: sum(val) / len(val) for key, val in combos.items()}

        for combo in adj_percent:
            if not all_holecard_percentages[str(num_players)].get(combo):
                all_holecard_percentages[str(num_players)][combo] = []
            all_holecard_percentages[str(num_players)][combo] += [adj_percent[combo]]


for player in all_holecard_percentages:
    for combo, val_list in all_holecard_percentages[player].items():
        all_holecard_percentages[player][combo] = 1.0 * sum(val_list) / len(val_list)

with open("./dart_lookups/complete_percentages.json", "w") as jsonFile:
    sanitized = {}
    for player in all_holecard_percentages:
        sanitized[player] = {}
        for key in all_holecard_percentages[player]:
            name = key[0] + ',' + ",".join(key[1])
            sanitized[player][name] = all_holecard_percentages[player][key]

    json.dump(sanitized, jsonFile)
