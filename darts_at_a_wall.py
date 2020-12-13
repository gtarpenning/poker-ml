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


def shuffle_and_draw():
    deck = utils.make_deck().copy()
    random.shuffle(deck)
    board = tuple(deck[:5])
    deck = deck[5:]

    return deck, board


all_holecard_percentages = {}
for num_players in range(2, NUM_PLAYERS + 1):
    print("Calculating holecard % for", num_players, "players using", EPOCHS, "epochs")
    all_holecard_percentages[str(num_players)] = {}
    hand_wins = defaultdict(int)
    hand_plays = defaultdict(int)
    for i in tqdm(range(EPOCHS)):
        deck, board = shuffle_and_draw()
        hands = []
        for i in range(num_players):
            h = tuple(deck[i * 2: (i + 1) * 2])
            if utils.c_lookup[h[0][0]] < utils.c_lookup[h[1][0]]:
                h = (h[1], h[0])
            elif h[0][0] == h[1][0] and h[0][1] < h[1][1]:
                h = (h[1], h[0])

            hands += [(h, compute.get_score(h + board))]
            hand_plays[h] += 1

        winner_hands = sorted(hands, key=operator.itemgetter(1), reverse=True)
        if winner_hands[0][1] > winner_hands[1][1]:  # Clear winner
            hand_wins[winner_hands[0][0]] += 1
        else:  # ties
            winning_val = winner_hands[0][1]
            for hand in winner_hands:
                if hand[1] == winning_val:
                    hand_wins[hand[0]] += 0.5
                else:
                    break

    # Assert every hole card pair is seen at least once
    assert(len(hand_plays) == 1326)
    hand_win_percents = {key: val / hand_plays[key] for key, val in hand_wins.items()}
    # average over hands of similar type
    combos = utils.get_combos_from_hand_dict(hand_win_percents)
    adj_percent = {key: sum(val) / len(val) for key, val in combos.items()}
    h = sorted(adj_percent.items(), key=lambda x: x[1], reverse=True)
    for up in h:
        print(up[0], up[1])

    for combo in adj_percent:
        all_holecard_percentages[str(num_players)][combo] = adj_percent[combo]

with open("./dart_lookups/hole_card_percentages.json", "w") as jsonFile:
    json.dump(all_holecard_percentages, jsonFile)
