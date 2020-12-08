import random
from abc import abstractmethod
import treys as Treys
from itertools import combinations
import numpy as np
import json

import utils
import compute

NUM_ROUNDS_PER_BB = 100
NUM_PLAYERS = 3
STARTING_STACK = 10000
NUM_ROUNDS = 1000
STARTING_BB = 10


class Player:
    def __init__(self, num, stack):
        self.num = num
        self.stack = stack
        self.hand = []
        self.chips_in_front = 0

    @abstractmethod
    def get_bet(self, table):
        raise NotImplementedError


class GTOMean(Player):
    pass


class GTOMedian(Player):
    def __init__(self):
        hole_data = json.load(open('hole_card_winning_percentages_median.json'))
        flop_data = json.load(open('flop_winning_percentages_median.json'))
        turn_data = json.load(open('turn_winning_percentages_median.json'))
        river_data = json.load(open('river_winning_percentages_median.json'))
        self.hole_card_percentages = utils.get_hand_dict_from_combos(hole_data)
        self.flop_percentages = utils.get_hand_dict_from_combos(flop_data)
        self.turn_percentages = utils.get_hand_dict_from_combos(turn_data)
        self.river_percentages = utils.get_hand_dict_from_combos(river_data)

    def get_pot_odds(self, table):
        return table.current_bet / (table.current_bet + table.pot)

    def get_equity(self, table):
        if len(table.board) == 0:    # Hole Cards.
            return self.hole_card_percentages[self.hand]
        elif len(table.board) == 3:  # Flop
            return self.flop_percentages[(self.hand, table.board)]
        elif len(table.board) == 4:  # Turn
            return self.turn_percentages[(self.hand, table.board)]
        else:                        # River
            return self.river_percentages[(self.hand, table.board)]

            """
            deck = utils.Poker.deck
            for card in cards:
                deck.remove(card)

            board_combos = [x for x in combinations(deck, 7 - len(cards))]
            cum_score = []
            for board in board_combos:
                cum_score += [compute.get_score(cards + board)]

            score = round(np.median(cum_score), 4)
            ave_score = None"""

    def get_bet(self, table):
        num_players = len(table.players)
        equity = self.get_equity(table)
        winning_percentage = equity[num_players]


class NaivePlayer(Player):

    def get_bet(self, table):
        raw = 0
        if len(table.board) == 0:  # major hack for evaluate function
            raw = table.evaluator.evaluate(self.hand, [Treys.Card.new('2h'), Treys.Card.new('3s'), Treys.Card.new('5c')])
        else:
            raw = table.evaluator.evaluate(self.hand, table.board)

        win_percent = 1 - table.evaluator.get_five_card_rank_percentage(raw)
        bet_size = 1.0 * table.current_bet / (table.pot + table.current_bet)

        if win_percent > bet_size:  # Should be calling or raising here.
            # With randomness, decide whether to call or raise
            raise_bool = random.uniform(0, win_percent) < (win_percent - bet_size)
            if raise_bool:
                return random.randint(table.current_bet, int((2 * win_percent * table.pot) + (table.pot / 2)))
            else:
                return table.current_bet
        else:  # Balance our strategy, also call sometimes with worse hands
            if table.current_bet == 0 or self.chips_in_front == table.current_bet:
                return table.current_bet

            if random.uniform(0, bet_size) < (win_percent * 0.8):
                return table.current_bet
            else:
                return None


class RandomPlayer(Player):

    def get_bet(self, table):
        if random.randint(0, len(table.players) - 1) > 0:  # CHECK FOLD
            if table.current_bet == 0 or self.chips_in_front == table.current_bet:  # CHECK
                return table.current_bet
            else:  # FOLD
                return None
        elif random.randint(0, 3) > 1:  # CHECK / CALL
            return table.check_legal_bet(table.current_bet, self.stack)
        else:  # TRY RAISE
            bet = random.randint(int(table.pot / 2), table.pot)
            legal_bet = table.check_legal_bet(bet, self.stack)

            return legal_bet


class ManualPlayer(Player):

    def get_bet(self, table):
        while True:
            bet = int(input(f'Enter bet for player {self.num}. (-1 to fold)'))
            legal_bet = table.check_legal_bet(bet, self.stack)
            if bet == -1:
                return None
            elif bet == legal_bet:
                return bet
            else:
                print(f"Illegal bet for player {self.num}")
                print(f"Player {self.num} stack: {self.stack}")


class ManualPlayerAssist(Player):

    def get_bet(self, table):  # NOT IMPLEMENTED PROPERLY #
        while True:
            print(f"Evalator win percentage for player {self.num}: %{0}. (-1 to fold)")
            bet = int(input(f'Enter bet for player {self.num}'))
            legal_bet = table.check_legal_bet(bet, self.stack)
            if bet == -1:
                return None
            elif bet == legal_bet:
                return bet
            else:
                print(f"Illegal bet for player {self.num}")
                print(f"Player {self.num} stack: {self.stack}")


class Table():

    def __init__(self, num_players, starting_big_blind, hands_per_bb):
        self.players = []
        self.order = [i for i in range(num_players)]
        self.board = []
        self.active = [True for x in range(num_players)]
        self.deck = Treys.Deck()
        self.evaluator = Treys.Evaluator()
        self.big_blind = starting_big_blind
        self.pot = 0
        self.current_bet = 0
        self.hands_per_bb = hands_per_bb
        self.round_counter = 0
        self.aggressor = None

    def check_legal_bet(self, bet, stack):
        if bet >= stack:
            return stack
        elif bet < self.current_bet:
            return self.current_bet
        elif bet >= self.current_bet * 2:
            formd = (bet // self.big_blind) * self.big_blind
            assert(formd >= self.current_bet)
            return formd
        else:  # Illegal bet larger than current bet, but not 2x
            return self.current_bet

    def facilitate_bet(self, player, bet, blind=False):
        if blind and bet == self.big_blind:
            print(f"Player {player.num} (BB) antes: ${bet}")
        elif blind:
            print(f"Player {player.num} (SB) antes: ${bet}")
        elif bet is None:
            print(f"Player {player.num} folds.")
            return
        elif (bet == 0 and self.current_bet == 0) or (player == self.aggressor and player.chips_in_front == bet):
            print(f"Player {player.num} checks.")
            return
        elif bet == player.stack:
            print(f"Player {player.num} goes ALL IN for: ${bet}")
        elif bet == self.current_bet:
            print(f"Player {player.num} calls with: ${bet}.")
        elif bet > self.current_bet:
            print(f"Player {player.num} raises to: ${bet}.")
            self.aggressor = player
        else:
            print("???", bet, self.current_bet, player.stack)
            raise

        assert(bet > player.chips_in_front)

        player.stack -= (bet - player.chips_in_front)
        player.chips_in_front = bet

        assert(player.stack >= 0)

    def reset_round(self):
        """Call before each hand, including first hand."""
        self.round_counter += 1
        self.order = self.order[1:] + [self.order[0]]
        self.active = [True for x in range(len(self.players))]
        self.deck = Treys.Deck()
        self.board = []
        self.pot = 0
        self.current_bet = 0

        # Handle big blind if needed
        if self.round_counter % (self.hands_per_bb * len(self.players)) == 0:
            self.big_blind *= 2

    def do_betting_round(self):
        checks = 0
        while True:
            for i in self.order:
                if not self.active[i]:
                    continue

                player = self.players[i]
                if (checks >= self.active.count(True)):  # or (self.active.count(True) == 1
                    # Done with betting round, action gets back to aggressor
                    for j in self.order:
                        if self.active[j]:
                            self.pot += self.players[j].chips_in_front
                            self.players[j].chips_in_front = 0
                    self.current_bet = 0
                    self.aggressor = None
                    return

                bet = player.get_bet(self)
                self.facilitate_bet(player, bet)
                if bet is None:  # Player Folds
                    self.active[i] = False
                    self.pot += player.chips_in_front
                    player.chips_in_front = 0
                else:
                    if bet > self.current_bet:  # Player Raises
                        checks = 1
                        self.current_bet = bet
                    else:  # Player Checks
                        checks += 1

    def do_preflop(self):
        sb = self.players[self.order[0]]
        self.facilitate_bet(sb, self.big_blind / 2, blind=True)

        bb = self.players[self.order[1]]
        self.facilitate_bet(bb, self.big_blind, blind=True)
        self.aggressor = bb
        self.current_bet = self.big_blind

        original_order = self.order.copy()
        self.order = self.order[2:] + self.order[:2]  # Ante Order
        self.do_betting_round()
        self.order = original_order

        if self.active.count(True) == 1:
            num = self.active.index(True)
            return self.players[num]
        elif self.active.count(True) == 0:
            print("No actives?")
            raise

    def do_round(self, num_cards):
        if num_cards > 1:
            self.board += self.deck.draw(num_cards)
        else:
            self.board += [self.deck.draw(num_cards)]
        print("BOARD: ", Treys.Card.print_pretty_cards(self.board))
        self.do_betting_round()

        if self.active.count(True) == 1:
            num = self.active.index(True)
            return self.players[num]
        elif self.active.count(True) == 0:
            print("No actives?")
            raise

    def do_hand(self):
        print(f"\n*Hand number: {self.round_counter}*")
        for i in self.order:
            self.players[i].hand = self.deck.draw(2)
        # ANTE
        winner = self.do_preflop()
        if winner:
            return winner
        # FLOP
        winner = self.do_round(3)
        if winner:
            return winner
        # TURN
        winner = self.do_round(1)
        if winner:
            return winner
        # RIVER
        winner = self.do_round(1)
        if winner:
            return winner
        # SHOWDOWN
        best = 8000
        winner = None
        for i in self.order:
            if self.active[i]:
                score = self.evaluator.evaluate(self.players[i].hand, self.board)
                if score < best:
                    best = score
                    winner = self.players[i]

        return winner


def run_game():
    """Run all components of the game."""
    table = Table(NUM_PLAYERS, STARTING_BB, NUM_ROUNDS_PER_BB)

    table.players += [NaivePlayer(0, STARTING_STACK)]
    for i in range(1, NUM_PLAYERS):
        table.players += [RandomPlayer(i, STARTING_STACK)]

    for round in range(NUM_ROUNDS):
        table.reset_round()
        winner = table.do_hand()

        print(f"Winner: Player {winner.num}, winning pot: ${table.pot}")
        winner.stack += table.pot
        for player in table.players:
            print("Player:", player.num, Treys.Card.print_pretty_cards(player.hand))

    print(f"\n\nAfter {NUM_ROUNDS} rounds, the player stacks are:")
    for player in table.players:
        print(f"Player {player.num}: ${player.stack}")


if __name__ == "__main__":
    run_game()
