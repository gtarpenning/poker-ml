from collections import defaultdict
from tqdm import tqdm
import operator
import random
import json
# local imports
import compute
import utils


EPOCHS = 1000000  # 1 million
NUM_PLAYERS = 9

hand_wins = defaultdict(int)
hand_plays = defaultdict(int)

c_lookup = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, 'T': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

all_holecard_percentages = {}

for num_players in range(2, NUM_PLAYERS + 1):
    print("Calculating holecard % for", num_players, "players using", EPOCHS, "epochs")
    all_holecard_percentages[str(num_players)] = {}
    for i in tqdm(range(EPOCHS)):
        deck = utils.make_deck().copy()
        random.shuffle(deck)
        board = tuple(deck[:5])
        deck = deck[5:]

        hands = []
        for i in range(num_players):
            h = tuple(deck[i * 2: (i + 1) * 2])
            if c_lookup[h[0][0]] < c_lookup[h[1][0]]:
                h = (h[1], h[0])
            elif h[0][0] == h[1][0] and h[0][1] < h[1][1]:
                h = (h[1], h[0])

            hands += [(h, compute.get_score(h + board))]
            hand_plays[h] += 1

        winner_hands = sorted(hands, key=operator.itemgetter(1), reverse=True)
        if winner_hands[0][1] > winner_hands[1][1]:
            hand_wins[winner_hands[0][0]] += 1
        else:  # tie (dont care about 3-way tie)
            hand_wins[winner_hands[0][0]] += 0.5
            hand_wins[winner_hands[1][0]] += 0.5

    hand_win_percents = {key: val / hand_plays[key] for key, val in hand_wins.items()}

    assert(len(hand_win_percents) == 1326)

    # average over hands of similar type
    combos = {}
    for (card1, card2) in hand_win_percents.keys():
        name = f"{card1[0]}{card2[0]}"
        if combos.get(f"{card2[0]}{card1[0]}"):
            name = f"{card2[0]}{card1[0]}"

        if card1[-1] != card2[-1] and card1[0] != card2[0]:  # off suited
            name += 'o'

        if not combos.get(name):
            combos[name] = []

        combos[name] += [hand_win_percents[(card1, card2)]]

    adj_percent = {key: sum(val) / len(val) for key, val in combos.items()}
    # h = sorted(adj_percentages.items(), key=lambda x: x[1], reverse=True)

    for combo in adj_percent:
        all_holecard_percentages[str(num_players)][combo] = adj_percent[combo]

with open("./dart_lookups/hole_card_percentages.json", "w") as jsonFile:
    json.dump(all_holecard_percentages, jsonFile)
