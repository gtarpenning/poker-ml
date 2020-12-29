import numpy as np
import random
from collections import Counter
from tqdm import tqdm
from datetime import datetime
from multiprocessing import Pool


"""
9 Unique Hand Score Types:

High Card:      0    + 0-13
One Pair:       14   + 0-13
Two Pair:       2*14 + 0-13
Thruple:        3*14 + 0-13 
Straight:       4*14 + 
Flush:          5*14 + 
Full House:     6*14 + 
Four of a Kind: 7*14 + 
Straight Flush: 8*14 + 

"""

score_lookup = {
    'high': 0,
    'one': 14,
    'two': 14*2,
    'thruple': 14*3,
    'straight': 4*14,
    'flush': 5*14,
    'full': 6*14,
    'four': 7*14,
    'straightflush': 8*14,
}


SUITS = [0, 1, 2, 3]
CARDS = list(range(0, 14))


def make_deck():
    d = [(x, y) for x in CARDS for y in SUITS]
    random.shuffle(d)
    return d


def get_score(hand):
    cards = sorted(hand, key=lambda x: x[0], reverse=True)
    nums = Counter([x[0] for x in hand])
    suits = Counter([x[1] for x in hand])
    # Check Straight
    straight_counter = 0
    prev_card = None
    for card in nums:
        if not prev_card:
            prev_card = card
            continue
        if card == prev_card - 1:
            straight_counter += 1
        if straight_counter == 4:
            break
        elif straight_counter == 3 and card == 2 and nums.get(13):  # Ace low straight
            straight_counter += 1
            break
        prev_card = card

    # Check Flush
    flush_suit = None
    for suit, val in suits.items():
        if val >= 5:
            flush_suit = suit

    # Check Straight Flush
    if straight_counter == 4 and flush_suit:  # Straight Flush!
        return score_lookup.get('straightflush') + prev_card + 3

    # 4 of a kind
    threes = []
    twos = []
    for num, val in nums.items():
        if val == 4:
            if cards[0][0] != num:
                return score_lookup.get('four') + num + cards[0][0]
            return score_lookup.get('four') + num + cards[4][0]
        elif val == 3:
            threes += [val]
        elif val == 2:
            twos += [val]

    # check full, thruple, two-pair
    if len(threes) == 2:
        return score_lookup.get('full') + max(threes) + min(threes) / 14
    elif len(threes) == 1 and len(twos) >= 1:
        return score_lookup.get('full') + threes[0] + max(twos) / 14
    elif not flush_suit and straight_counter != 4:
        highs = [val for val in nums if val not in threes and val not in twos]
        if len(threes) == 1:  # Thruple
            return score_lookup.get('thruple') + threes[0] + (highs[0] / 14) + (highs[1] / (14 ** 2))
        elif len(twos) >= 2:  # Two Pair
            top = max(twos)
            twos.remove(top)
            bottom = max(twos)
            return score_lookup.get('two') + top + (bottom / 14) + (highs[0] / (14 ** 2))
        elif len(twos) == 1:  # One pair
            return score_lookup.get('one') + twos[0] + (highs[0] / 14) + (highs[1] / (14 ** 2)) + (highs[2] / (14 ** 3))
        else: # High Card
            return score_lookup.get('high') + highs[0] + (highs[1] / 14) + (highs[1] / (14 ** 2)) + (highs[2] / (14 ** 3)) + (highs[3] / (14 ** 4))

    # flush
    if flush_suit:
        return score_lookup.get('flush') + sum([x[0] / (14 ** (i+1)) for i, x in enumerate(cards) if x[1] == flush_suit][:5])

    # straight
    if straight_counter == 4:
        return score_lookup.get('straight') + prev_card + 3


def main(EPOCHS):
    deck = make_deck()
    random.shuffle(deck)
    hand = deck[:7]
    get_score(hand)


if __name__ == "__main__":
    EPOCHS = [0 for x in range(1000000)]
    start = datetime.now()
    with Pool() as p:
        p.map(main, EPOCHS)

    print("seconds:", datetime.now() - start)
