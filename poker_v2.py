import random
from abc import abstractmethod
import treys
import json
# local imports
import utils
# import compute

NUM_ROUNDS_PER_BB = 100
NUM_PLAYERS = 3
STARTING_STACK = 100000
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


class GTOPlayer(Player):
    def __init__(self, num, stack, var=0.15):
        super().__init__(num, stack)
        self.hole_card_percentages = json.load(open('./dart_lookups/hole_card_percentages.json'))
        self.defensive_variation = var

    def get_pot_odds(self, current_bet, pot):
        return current_bet / (current_bet + pot)

    def get_equity(self, table, num_players):
        if len(table.board) == 0:    # Hole Cards.
            combo_name = utils.get_combo_from_hand(self.hand)
            equity = self.hole_card_percentages[str(num_players)][combo_name]
            print(f"got GTO equity for hole cards {self.hand} as: [{equity}]")
            return equity
        else:
            # use Treys
            b = [treys.Card.new(x) for x in table.board]
            h = [treys.Card.new(x) for x in self.hand]
            raw = table.evaluator.evaluate(h, b)
            raw_win_percent = 1 - table.evaluator.get_five_card_rank_percentage(raw)

            print(raw, raw_win_percent, raw_win_percent - (((num_players - 2) * 8) / 100))

            return raw_win_percent - (0.14 / (num_players - 2))

    def get_bet(self, table):
        num_players = len(table.players)
        pot, min_call = table.get_adjusted_pot(), table.current_bet - self.chips_in_front

        equity = self.get_equity(table, num_players)
        expected_value = equity * pot
        pot_odds = self.get_pot_odds(min_call, pot)
        min_bet = max(table.current_bet * 2, table.big_blind)

        print("pot:", pot, "equity:", equity, "pot odds:", pot_odds, "ev:", expected_value, "min_call:", min_call)
        print("min_bet", min_bet, "ev_bet:", equity * (pot + 2*min_bet) - min_bet, "ev_call:", equity * (pot + 2*min_call) - min_call)

        if equity < pot_odds:  # Check fold
            if min_call == 0:  # CHECK
                return 0
            else:  # fold
                return None
        elif min_call == 0 and (equity - pot_odds) * pot < table.big_blind:  # check
            return table.current_bet
        elif equity * (pot + table.current_bet * table.active.count(True)) - table.current_bet < min_bet:  # call
            return table.current_bet
        else:  # Raise / bet
            ran = int(table.big_blind * 2 * self.defensive_variation)
            val = table.current_bet + int(expected_value) + random.randint(-ran, ran)

            if min_bet > val > min_bet * 0.8:
                return min_bet  # stretch bet to minimum allowed
            elif val < min_bet:
                return table.current_bet  # abort bet, just call

            return val


class NaivePlayer(Player):

    def get_bet(self, table):
        to_eval = []
        if len(table.board) == 0:  # major hack for evaluate function
            to_eval = [treys.Card.new(card) for card in ['2h', '5s', '7c']]
        else:
            to_eval += [treys.Card.new(card) for card in table.board]

        raw = table.evaluator.evaluate([treys.Card.new(x) for x in self.hand], to_eval)

        win_percent = 1 - table.evaluator.get_five_card_rank_percentage(raw)
        adj_pot = table.get_adjusted_pot()
        bet_size = 1.0 * table.current_bet / (adj_pot + table.current_bet)

        if win_percent > bet_size:  # Should be calling or raising here.
            # With randomness, decide whether to call or raise
            raise_bool = random.uniform(0, win_percent) < (win_percent - bet_size)
            if raise_bool:
                min_bet = max(table.current_bet, table.big_blind)
                bet = random.randint(min_bet, int((2 * win_percent * adj_pot) + (adj_pot / 2))+5)
                return bet
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
            bet = int(input(f"Enter bet for player {self.num}. (-1 to fold)"))
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
            print(f"Evaluator win percentage for player {self.num}: %{0}. (-1 to fold)")
            bet = int(input(f"Enter bet for player {self.num}"))
            legal_bet = table.check_legal_bet(bet, self.stack)
            if bet == -1:
                return None
            elif bet == legal_bet:
                return bet
            else:
                print(f"Illegal bet for player {self.num}")
                print(f"Player {self.num} stack: {self.stack}")


class Table:

    def __init__(self, num_players, starting_big_blind, hands_per_bb):
        self.players = []
        self.order = [i for i in range(num_players)]
        self.board = []
        self.active = [True for _ in range(num_players)]
        self.deck = utils.make_deck()
        self.evaluator = treys.Evaluator()
        self.big_blind = starting_big_blind
        self.pot = 0
        self.current_bet = 0
        self.hands_per_bb = hands_per_bb
        self.round_counter = 0
        self.aggressor = None

    def get_adjusted_pot(self):
        pot = self.pot
        for player in self.players:
            pot += player.chips_in_front

        return pot

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
        self.active = [True for _ in range(len(self.players))]
        self.deck = utils.make_deck()
        self.board = []
        self.pot = 0
        self.current_bet = 0

        random.shuffle(self.deck)

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
                if checks >= self.active.count(True):  # or (self.active.count(True) == 1
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
        self.board += self.deck[:num_cards]
        self.deck = self.deck[num_cards:]

        print("BOARD: ", self.board)
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
            self.players[i].hand = self.deck[:2]
            self.deck = self.deck[2:]

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
        treys_board = [treys.Card.new(card) for card in self.board]
        for i in self.order:
            if self.active[i]:
                score = self.evaluator.evaluate([treys.Card.new(card) for card in self.players[i].hand], treys_board)
                if score < best:
                    best = score
                    winner = self.players[i]

        return winner


def main():
    """Run all components of the game."""
    # Make table
    table = Table(NUM_PLAYERS, STARTING_BB, NUM_ROUNDS_PER_BB)

    # Make players
    table.players += [NaivePlayer(0, STARTING_STACK)]
    table.players += [GTOPlayer(1, STARTING_STACK)]
    for i in range(2, NUM_PLAYERS):
        table.players += [RandomPlayer(i, STARTING_STACK)]

    assert(NUM_PLAYERS == len(table.players))

    # Handle scoring / winners
    for _ in range(NUM_ROUNDS):
        table.reset_round()
        winner = table.do_hand()

        print(f"Winner: Player {winner.num}, winning pot: ${table.pot}")
        winner.stack += table.pot
        for player in table.players:
            print(f"Player: {player.num} hand: {player.hand}")

    print(f"\n\nAfter {NUM_ROUNDS} rounds, the player stacks are:")
    for player in table.players:
        print(f"Player {player.num}: ${player.stack}")


if __name__ == "__main__":
    main()
