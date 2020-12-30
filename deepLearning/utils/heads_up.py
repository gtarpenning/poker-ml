SUITS = ['h', 's', 'd', 'c']
CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
DECK = [c + s for c in CARDS for s in SUITS]
CARD_DICT = {DECK[i]:i for i in range(len(DECK))}

import random
import torch
import torch.nn as nn
import treys
from treys import Evaluator
from treys import Card


def one_hot_cards(cards, card_dict=CARD_DICT, device='cpu', dtype=torch.float):
    """
    cards is an iterable of 2 char string that shows the number and then suit
    We're going to one hot encode these cards in a 52 long vector
    """
    ret = torch.zeros(52, dtype = dtype).to(device)
    for card in cards:
        ret[card_dict[card]] = 1
    return ret

#! THIS IS COPIED CODE FROM poker-ml/utils.py
def make_deck():
    deck = DECK
    random.shuffle(deck)
    return deck

def make_heads_up():
    """
    Makes a heads up game
    Each hand and board is a list of 2 char strings encoding the cards
    Returns: (player_1_hand, player_2_hand, board)
    """
    deck = make_deck()
    return (deck[:2], deck[2:4], deck[4:9])
    
def make_treys(cards):
    """
    Converts iterable of cards encoded as '2h' to treys.Card.new() objects
    """
    return [Card.new(c) for c in cards]

def score_heads_up(p1, p2, board):
    """
    p1, p2, board are iterables of 2char encoded cards
    returns tuple of 1 if player wins and 0 of player loses # ties are both 1
    """
    player1 = make_treys(p1)
    player2 = make_treys(p2)
    b = make_treys(board)
    e = Evaluator()
    # as ugly as the below three lines are they're the fastest method of doing this IMO.
    s1 = e.evaluate(player1, b)
    s2 = e.evaluate(player2, b)
    return (int(s1 <= s2), int(s1 >= s2))