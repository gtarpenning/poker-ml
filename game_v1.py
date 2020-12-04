import random

from treys import Card, Deck, Evaluator


START_STACK = 1000
NUM_PLAYERS = 4
BIG_BLIND = 10


class Player:

    def __init__(self, num, stack, hand, role, strat='random'):
        self.num = num
        self.stack = stack
        self.hand = hand
        self.strat = strat
        self.role = role
        self.last_bet = 0


class Game:

    def __init__(self):
        self.evaluator = Evaluator()
        self.deck = Deck()
        self.board = []
        self.players = [Player(i + 1, START_STACK, [], i + 1) for i in range(NUM_PLAYERS)]
        self.actives = [i + 1 for i in range(len(self.players))]
        self.pot = 0
        self.current_bet = 0

        self.big_blind = BIG_BLIND
        self.small_blind = BIG_BLIND / 2

    def new_hand(self):
        self.deck = Deck()
        self.board = []
        self.actives = [i + 1 for i in range(NUM_PLAYERS)]
        self.pot = 0
        self.current_bet = 0

        for player in self.players:
            player.role = (player.role % NUM_PLAYERS) + 1

        self.players = sorted(self.players, key=lambda x: x.role, reverse=False)

    def is_active(self, player):
        if player.num in self.actives:
            return True
        return False

    def get_player_bet(self, player):
        """Returns int for chips to invest."""
        if player.strat == 'naive':
            raw = 0
            if len(self.board) == 0:
                # Hack this because it can't evaluate without a board

                raw = self.evaluator.evaluate(player.hand, [Card.new('2h'), Card.new('3s'), Card.new('5c')])
            else:
                raw = self.evaluator.evaluate(player.hand, self.board)

            percent = 1 - self.evaluator.get_five_card_rank_percentage(raw)
            return int(percent * self.pot)

        elif player.strat == 'manual':
            return int(input('Enter bet for player {}'.format(player.num)))
        elif player.strat == 'manual-assist':
            percent = self.evaluator.evaluate(player.hand, self.board)
            return int(input('Enter bet for player {}, win rate: {}'.format(player.num, percent)))
        elif player.strat == 'random':
            fold = random.randint(0, len(self.actives) - 1)
            if fold > 0:  # FOLD
                return 0
            else:
                if self.pot == 0:
                    return random.randint(self.big_blind, self.big_blind * 2)
                else:
                    return random.randint(int(self.pot / 2), self.pot)
        elif player.strat == 'GTO':
            print("GTO not implemented yet.")
            raise
        else:
            print("Unknown strategy for player {}".format(player.num))
            raise

    def betting_round(self, is_ante):
        """No card handling, only betting."""
        self.current_bet = 0
        for player in self.players:
            player.last_bet = 0
        round_num = 0
        while True:
            round_num += 1
            for player in self.players:
                if not self.is_active(player):
                    continue

                if round_num > 1:
                    if (is_ante and player.role != 2) and player.last_bet == self.current_bet:  # Completed Betting Round
                        return

                    non_complete = [x for x in self.players if (self.is_active(x) and x.last_bet != self.current_bet)]
                    if len(non_complete) == 0 or len(self.actives) == 1:
                        return

                if is_ante and round_num == 1 and player.role in [1, 2]:
                    if player.role == 1:
                        self.current_bet = self.small_blind
                    elif player.role == 2:
                        self.current_bet = self.big_blind
                    player.stack -= self.current_bet
                    self.pot += self.current_bet
                    player.last_bet = self.current_bet
                    print(f"Player {player.num} bets: ${self.current_bet}.")
                else:
                    bet = self.get_player_bet(player)
                    bet_adj = min((bet // self.big_blind) * self.big_blind, player.stack)

                    if (bet_adj == 0 or bet_adj < self.current_bet) and self.current_bet > 0 and player.last_bet != self.current_bet:
                        print(f"Player {player.num} folds.")
                        self.actives.remove(player.num)
                        player.active = False
                    elif (bet_adj == 0 and self.current_bet == player.last_bet) or (player.role == 2 and bet_adj == 0):
                        print(f"Player {player.num} checks.")
                    elif self.current_bet == 0:
                        print(f"Player {player.num} bets: ${bet_adj}.")
                        self.current_bet = bet_adj
                        player.stack -= self.current_bet
                        self.pot += self.current_bet
                        player.last_bet = self.current_bet
                    else:  # CALL
                        call = self.current_bet - player.last_bet
                        print(f"Player {player.num} calls: ${call}.")
                        player.stack -= call
                        self.pot += call
                        player.last_bet = self.current_bet

    def do_turn(self, num_cards):
        if num_cards == 3:
            self.betting_round(True)
            for card in self.deck.draw(num_cards):
                self.board += [card]
        else:
            self.betting_round(False)
            self.board += [self.deck.draw(num_cards)]

        print("BOARD:  ", Card.print_pretty_cards(self.board))

    def run_game(self):
        """Structure of play."""
        self.players[0].strat = 'naive'
        self.players[1].strat = 'naive'
        for i in range(10):
            print("Current Stack Sizes: ")
            for player in self.players:
                print(f"Player {player.num}: ${player.stack}")
            print(f"\n***** Hand {i+1} *****")
            self.new_hand()

            for player in self.players:
                player.hand = self.deck.draw(2)

            for player in self.players:
                print(f"Player {player.num}", Card.print_pretty_cards(player.hand))

            self.do_turn(3)
            if len(self.actives) == 1:
                winner = sorted(self.players, key=lambda x: x.num)[self.actives[0] - 1]
                print(f"Winner: Player {winner.num}, winning pot: ${self.pot}")
                winner.stack += self.pot
                continue

            self.do_turn(1)
            if len(self.actives) == 1:
                winner = sorted(self.players, key=lambda x: x.num)[self.actives[0] - 1]
                print(f"Winner: Player {winner.num}, winning pot: ${self.pot}")
                winner.stack += self.pot
                continue

            self.do_turn(1)
            if len(self.actives) == 1:
                winner = sorted(self.players, key=lambda x: x.num)[self.actives[0] - 1]
                print(f"Winner: Player {winner.num}, winning pot: ${self.pot}")
                winner.stack += self.pot
                continue

            self.betting_round(False)
            if len(self.actives) == 1:
                winner = sorted(self.players, key=lambda x: x.num)[self.actives[0] - 1]
                print(f"Winner: Player {winner.num}, winning pot: ${self.pot}")
                winner.stack += self.pot
            else:
                best = 8000
                winner = None
                for player in self.players:
                    if self.is_active(player):
                        score = self.evaluator.evaluate(player.hand, self.board)
                        if score < best:
                            best = score
                            winner = player
                print(f"Winner: Player {winner.num}, winning pot: ${self.pot}")
                winner.stack += self.pot

        print("\n**** Final Stack Sizes: ")
        for player in self.players:
            print(f"Player {player.num}: ${player.stack}")


Game().run_game()
