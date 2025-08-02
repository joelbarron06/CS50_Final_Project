import random
import requests
import re
import textwrap
from datetime import datetime
import sys


class Card:
    """
    Class for giving the properties of each card in the deck
    Initalise the rank, suit and value of the card (ace value handled in game - base 11)
    Set up ascii art for each card
    """

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = self.get_value()

    def __str__(self):
        if (
            self.rank != "10"
        ):  # ascii art for cards: 10 is too digits so different spacing
            return f"""
┌───────────┐
│{self.rank}          │
│           │
|           |
│     {self.suit}     │
│           │
│           │
│          {self.rank}│
└───────────┘"""

        else:
            return f"""
┌───────────┐
│{self.rank}         │
│           │
|           |
│     {self.suit}     │
│           │
│           │
│         {self.rank}│
└───────────┘"""

    def get_value(self):
        if self.rank in ["J", "Q", "K"]:
            return 10
        elif self.rank == "A":
            return 11  # ace value handled later in hand based on other cards
        else:
            return int(self.rank)

    def get_lines(self):  # used when printing cards side by side
        return str(self).strip().split("\n")


class Deck:
    """
    Class for the deck, giving the size, shuffling mechanics, etc.
    Deck size and correct cards
    shuffling mechanics
    Draw card mechanics, and check if reshullfle/fresh deck needed
    """

    def __init__(self):
        self.cards = []
        self.num_decks = 6
        self.shuffle_point = 1
        self.reset_deck()  # deck is set when initalised

    def reset_deck(self):
        suits = ["♠", "♥", "♦", "♣"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.shuffle_point = round(
            random.uniform(0.6, 0.85), 2
        )  # this is a paramter for deciding when dekc needs reshuffled

        # create ordered deck
        for _ in range(self.num_decks):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(suit, rank))

        for _ in range(15):
            self.shuffle_deck()

        self.cards.pop()  # burn top card

    def shuffle_deck(self):
        # cards are cut in two (with error) and split into two piles
        cut = len(self.cards) // (2 + random.randint(-1, 3))
        left = self.cards[:cut]
        right = self.cards[cut:]

        shuffled_cards = []
        while left and right:

            # probability weighting in relation to pile size
            if len(left) > len(right):
                prob_left = 0.6
            elif len(right) > len(left):
                prob_left = 0.4
            else:
                prob_left = 0.5

            if random.random() < prob_left:
                shuffled_cards.append(left.pop(0))
            else:
                shuffled_cards.append(right.pop(0))

        # add remaining cards
        shuffled_cards.extend(left)
        shuffled_cards.extend(right)

        self.cards = shuffled_cards

    def draw_card(self):
        if len(self.cards) <= (self.num_decks * 52 * (1 - self.shuffle_point)):
            print("Shuffling deck...")
            self.reset_deck()

        return self.cards.pop()


class Hand:
    """
    Class for the player/dealer hand
    List of cards in hand
    Hand mechanics - hit, stand, split, bust
    Dynamic value of aces handled
    """

    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def __str__(self):

        if not self.cards:
            return  # avoids error for no cards

        all_lines = [card.get_lines() for card in self.cards]
        max_lines = max(len(lines) for lines in all_lines)

        # cards the cards in hand and forms a nested list, before reformatting to a string s.t. cards are side by side
        result_lines = []
        for line_num in range(max_lines):
            line = ""
            for card_lines in all_lines:
                if line_num < len(card_lines):
                    line += card_lines[line_num]
                else:
                    line += " " * 13
                line += "  "
            result_lines.append(line.rstrip())

        return "\n".join(result_lines)

    def add_card(self, card):
        self.cards.append(card)
        self.value += card.value
        if card.rank == "A":
            self.aces += 1
        self.ace_adjustment()

    def ace_adjustment(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    def is_bust(self):
        return self.value > 21

    def is_blackjack(self):
        if len(self.cards) != 2:
            return False

        has_ace = False
        has_ten = False

        for card in self.cards:
            if card.rank == "A":
                has_ace = True
            elif card.value == 10:
                has_ten = True

        return has_ace and has_ten


class User:
    """
    Class which sets up a user profile.
    Username must be set when calling the class
    Email can be added optinally with get_email method, and is automatically checked to see if it is valid
    """

    def __init__(self, username):
        self._username = username
        self._email = self.get_email()

    @property
    def email(self):
        return self._email

    @property
    def username(self):
        return self._username

    @email.setter  # chacks valid email form
    def email(self, value):
        if re.match(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", value, re.IGNORECASE):
            self._email = value
        else:
            raise ValueError

    def get_email(self):  # recursive on invalid email from setter
        try:
            email = input("Email: ").strip()
            self.email = email
            return email
        except ValueError:
            print("Invalid email address, please try again.")
            return self.get_email()


class Account:
    """
    The player's account, in which stats are stored for the summary, and payment is made.
    Can call print on account and prints the players stats and account details receipt style.
    """

    def __init__(self, user):
        self.user = user
        self.balance = 0
        self.bet = 0
        self.net_earnings = 0
        self.games_played = 0
        self.games_won = 0
        self.deposited = 0

    def __str__(self):  # easy way to print stats
        return textwrap.dedent(
            f"""\
                               ACCOUNT DETAILS
                               {'='*40}
                               Date: {datetime.today().strftime('%d/%m/%Y')}
                               Username: {self.user._username}
                               Email: {self.user._email}
                               Balance: ${self.balance:,.2f}
                               Hands Played: {self.games_played} ({self.get_win_rate():.1f}% win rate)
                               Amount Deposited: ${self.deposited:,.2f}
                               Amount Bet: ${self.bet:,.2f}
                               Earnings: ${self.net_earnings:,.2f}
                               Return on Wager: {self.get_roi():.1f}%
                               {'='*40}"""
        ).strip()

    def deposit(self):
        # option to choose what currency is deposited, with live price conversion to USD
        while True:
            currency = (
                input(
                    "What (crypto)currency would you like to pay with? Type currency code: "
                )
                .strip()
                .upper()
            )
            rate = None

            try:
                response = requests.get(
                    "https://api.coinbase.com/v2/exchange-rates?currency=USD"
                )
                data = response.json()["data"]["rates"]
                rate = float(data[currency])
                break
            except requests.RequestException:
                print("Conversion Error, please try again.")
                continue
            except KeyError:
                try:
                    response = requests.get(
                        "https://v6.exchangerate-api.com/v6/71ff41f4cf4c766926e513f5/latest/USD"
                    )
                    content = response.json()["conversion_rates"]
                    rate = float(content[currency])
                    break
                except requests.RequestException:
                    print("Conversion Error, please try again.")
                    continue
                except KeyError:
                    print(
                        "Invalid currency code. Note we only support payment from major cryptocurrencies."
                    )
                    continue

        while True:
            try:
                amount = float(
                    input("Set deposit amount (do not include currency sign): ").strip()
                )
                break
            except ValueError:
                print("Please enter numeric amount.")
                continue

        amount_usd = round((amount / rate), 2)
        input(f"You are depositing ${amount_usd:,.2f}. Press Enter to confirm.")
        self.balance += amount_usd
        self.deposited += amount_usd

    def cash_out(self):
        # as with deposit, choose currency and usd conterted to it; same API calls
        while True:
            currency = (
                input(
                    "What (crypto)currency would you like to be paid in? Type currency code: "
                )
                .strip()
                .upper()
            )
            rate = None

            try:
                response = requests.get(
                    "https://api.coinbase.com/v2/exchange-rates?currency=USD"
                )
                data = response.json()["data"]["rates"]
                rate = float(data[currency])
                break
            except requests.RequestException:
                print("Conversion Error, please try again.")
                continue
            except KeyError:
                try:
                    response = requests.get(
                        "https://v6.exchangerate-api.com/v6/71ff41f4cf4c766926e513f5/latest/USD"
                    )
                    content = response.json()["conversion_rates"]
                    rate = float(content[currency])
                    break
                except requests.RequestException:
                    print("Conversion Error, please try again.")
                    continue
                except KeyError:
                    print(
                        "Invalid currency code. Note we only support payment from major cryptocurrencies."
                    )
                    continue

        payment = self.balance * rate
        receipt = textwrap.dedent(
            f"""\
                               {'='*40}
                               RECEIPT
                               Date: {datetime.today().strftime('%d/%m/%Y')}
                               Username: {self.user._username}
                               Email: {self.user._email}
                               Payment: {payment:,.2f} {currency}
                               Hands Played: {self.games_played} ({self.get_win_rate():.1f}% win rate)
                               Return on Wager: {self.get_roi():.1f}%
                               {'='*40}
                               Thank you for playing.
                               {'='*40}"""
        ).strip()
        input(f"You will be paid {payment:,.2f} {currency}. Press Enter to confirm.")
        sys.exit(receipt)

    def get_roi(self):
        try:
            return (self.net_earnings / self.bet) * 100
        except ZeroDivisionError:
            return 0

    def get_win_rate(self):
        try:
            return (self.games_won / self.games_played) * 100
        except ZeroDivisionError:
            return 0

    def place_bet(self, amount):
        # places the bet if valid, denies if not, returns a BOOL based on a legal bet
        if self.balance >= amount:
            self.balance -= amount
            self.bet += amount
            self.net_earnings -= amount
            return True
        return False

    def game_won(self, amount):
        self.balance += amount
        self.net_earnings += amount
        self.games_won += 1


def main_menu(account):
    """
    Function which initaites main menu and validates user input
    Is called repeatedly by main function, until option 4 is called which ends with sys.exit
    """
    menu = f"""{'='*40}
Main Menu:
1) Play Game
2) View Account
3) Make Deposit
4) Cash Out and Exit
{'='*40}"""
    print(menu)
    while True:
        option = input("Select option (1-4): ")
        # validate input
        if option in ["1", "2", "3", "4"]:
            break
        print("Invalid Option")

    print("=" * 40)
    # evalute input
    if option == "1":
        if account.balance == 0:
            input(
                "You must add funds before you can play. Press Enter to return to Main Menu"
            )
            return
        deck = Deck()
        play_game(account, deck)
        return
    elif option == "2":
        print(account)
        input("Press Enter to Return to Main Menu")
        return
    elif option == "3":
        account.deposit()
        print(f"{'='*40}\nNew account balance: ${account.balance:,.2f}")
        return
    elif option == "4":
        if (
            account.deposited == 0
        ):  # ignores cashing out receipt if user has not desposited anything
            sys.exit(f"Thank you for playing.\n{'='*40}")
        else:
            account.cash_out()


def play_game(account, deck):
    """
    Function which goes though basic game mechanics
    Initiates the game and approtiate class objects created
    """
    account.games_played += 1
    bet = get_bet(account)

    dealer_hand = Hand()
    player_hand = Hand()

    # European dealing pattern
    player_hand.add_card(deck.draw_card())
    dealer_hand.add_card(deck.draw_card())
    player_hand.add_card(deck.draw_card())

    print("=" * 40)
    print("Dealer:", dealer_hand, sep="\n")
    print("Hand:", player_hand, sep="\n")

    if player_hand.is_blackjack():
        print("Blackjack!")
        if not dealer_play(player_hand, dealer_hand, deck):
            calculate_payoff(bet, "win", account, player_hand)
            input(f"Dealer bust! You win.\nHit enter to return to Main Menu.")
            return

        input(check_winner(player_hand, dealer_hand, account, bet))
        return

    actions = split_allowed(player_hand)
    action = get_action(actions, bet, account)

    if action == "H":
        if not hit(player_hand, dealer_hand, deck):
            input(f"Bust! Dealer wins.\nHit enter to return to Main Menu.")
            return

        if not dealer_play(player_hand, dealer_hand, deck):
            calculate_payoff(bet, "win", account, player_hand)
            input(f"Dealer bust! You win.\nHit enter to return to Main Menu.")
            return

        input(check_winner(player_hand, dealer_hand, account, bet))
        return

    elif action == "S":
        if not dealer_play(player_hand, dealer_hand, deck):
            calculate_payoff(bet, "win", account, player_hand)
            input(f"Dealer bust! You win.\nHit enter to return to Main Menu.")
            return

        input(check_winner(player_hand, dealer_hand, account, bet))
        return

    elif action == "D":
        player_hand.add_card(deck.draw_card())

        print("=" * 40)
        print("Dealer:", dealer_hand, sep="\n")
        print("Hand:", player_hand, sep="\n")

        if player_hand.is_bust():
            input(f"Bust! Dealer wins.\nHit enter to return to Main Menu.")
            return

        input("Hit enter to continue.")
        if not dealer_play(player_hand, dealer_hand, deck):
            calculate_payoff(bet * 2, "win", account, player_hand)
            input(f"Dealer bust! You win.\nHit enter to return to Main Menu.")
            return

        input(check_winner(player_hand, dealer_hand, account, bet * 2))
        return

    elif action == "L":
        split(player_hand, dealer_hand, deck, bet, account)

    return


def get_bet(account):
    # gets bet amount from user; checks is a float and sufficent funds; returns bet amount to save for double/split
    while True:
        try:
            bet = round(
                float(
                    input(f"Current balance ${account.balance:,.2f}\nSet bet amount: $")
                ),
                2,
            )
            if bet < 2:
                raise ValueError
            if not account.place_bet(bet):
                print(f"{'='*40}\nInsufficient funds.\n{'='*40}")
                continue

            break
        except ValueError:
            print("Bet must be dollar amount, minimum $2.")
            continue

    return bet


def split_allowed(hand):
    # determines what player actions are allowed based on hand (split)
    if hand.cards[0].value == hand.cards[1].value:
        return "Do you want to hit (H), stand (S), double (D) or split (L): "
    else:
        return "Do you want to hit (H) or stand (S), double (D): "


def get_action(actions, bet, account):
    while True:
        action = input(actions).upper()
        # validate input
        options = ["H", "S", "D"]
        if "split" in actions:
            options.append("L")
        elif action == "L":
            print("Splitting is not allowed on this hand.")
            continue

        if action in options:
            if action_allowed(bet, action, account):
                break
            else:
                print("Insufficient Funds")
                continue
        else:
            print("Invalid Action")
        continue

    return action


def action_allowed(bet, action, account):
    # return BOOL based on whether player can afford to split/double
    if action in ["H", "S"]:
        return True
    elif action in ["D", "L"]:
        if account.place_bet(bet):
            return True
    else:
        return False


def hit(hand, d_hand, deck):
    # repeated action for hit until player stands; returns BOOL - 0 for bust; 1 for legal
    while True:
        hand.add_card(deck.draw_card())

        print("=" * 40)
        print("Dealer:", d_hand, sep="\n")
        print("Hand:", hand, sep="\n")

        if hand.is_bust():
            return False

        while True:
            action = input("Do you want to hit (H) or stand (S): ").upper()
            if action in ["H", "S"]:
                break
            else:
                print("Invalid Action")
                continue

        if action == "S":
            return True


def split(hand, dealer_hand, deck, bet, account):
    # code to allow splitting player hand
    account.games_played += 1
    player_hand1 = Hand()
    player_hand2 = Hand()

    player_hand1.add_card(hand.cards[0])
    player_hand2.add_card(hand.cards[1])

    print("=" * 40)
    print("Dealer:", dealer_hand, sep="\n")
    print("Hand 1:", player_hand1, sep="\n")
    print("Hand 2:", player_hand2, sep="\n")

    input("Hit enter to deal...")
    player_hand1.add_card(deck.draw_card())
    player_hand2.add_card(deck.draw_card())
    print("=" * 40)
    print("Dealer:", dealer_hand, sep="\n")
    print("Hand 1:", player_hand1, sep="\n")
    print("Hand 2:", player_hand2, sep="\n")

    action1 = play_split(player_hand1, 1, deck, dealer_hand, bet, account)
    input("Hit enter to play next hand")
    print("=" * 40)
    print("Dealer:", dealer_hand, sep="\n")
    print("Hand 1:", player_hand1, sep="\n")
    print("Hand 2:", player_hand2, sep="\n")
    action2 = play_split(player_hand2, 2, deck, dealer_hand, bet, account)

    if not player_hand2.is_bust():
        split_dealer_play(player_hand1, player_hand2, dealer_hand, deck)
    elif not player_hand1.is_bust():
        split_dealer_play(player_hand1, player_hand2, dealer_hand, deck)
    else:
        input(f"Both bust! Dealer wins.\nHit enter to return to Main Menu.")
        return

    if dealer_hand.is_bust():
        if not player_hand1.is_bust():
            message1 = "You win!"
            if action1 == "D":
                calculate_payoff(bet * 2, "win", account, player_hand1, 1)
            else:
                calculate_payoff(bet, "win", account, player_hand1, 1)
        if not player_hand2.is_bust():
            message2 = "You win!"
            if action2 == "D":
                calculate_payoff(bet * 2, "win", account, player_hand2, 1)
            else:
                calculate_payoff(bet, "win", account, player_hand2, 1)
    else:
        if not player_hand1.is_bust():
            if action1 == "D":
                message1 = check_winner(player_hand1, dealer_hand, account, bet * 2, 1)
            else:
                message1 = check_winner(player_hand1, dealer_hand, account, bet, 1)
            message1 = message1.split("\n")[0]
        if not player_hand2.is_bust():
            if action2 == "D":
                message2 = check_winner(player_hand2, dealer_hand, account, bet * 2, 1)
            else:
                message2 = check_winner(player_hand2, dealer_hand, account, bet, 1)
            message2 = message2.split("\n")[0]

    print(f"Hand 1: {message1}\nHand 2: {message2}")
    input("Hit Enter to return to Main Menu.")
    return


def play_split(player_hand, hand_num, deck, dealer_hand, bet, account):
    # player actions for each hand in a split; further splitting not allowed
    print(f"PLAYING HAND {hand_num}:")
    action = get_action(
        "Do you want to hit (H) or stand (S), double (D): ", bet, account
    )

    if action == "H":
        if not hit(player_hand, dealer_hand, deck):
            print("Bust!")
            return
        return

    elif action == "S":
        return

    elif action == "D":
        player_hand.add_card(deck.draw_card())

        print("=" * 40)
        print("Dealer:", dealer_hand, sep="\n")
        print(f"Hand:", player_hand, sep="\n")

        if player_hand.is_bust():
            print(f"Bust!")
            return
        return "D"


def split_dealer_play(hand1, hand2, dealer_hand, deck):
    # dealer plays out after hands are split
    while dealer_hand.value < 17:
        dealer_hand.add_card(deck.draw_card())

        print("=" * 40)
        print("Dealer hits...")
        print("Dealer:", dealer_hand, sep="\n")
        print("Hand 1:", hand1, sep="\n")
        print("Hand 2:", hand2, sep="\n")

        if dealer_hand.is_bust():
            return
        if dealer_hand.value < 17:
            input("Hit enter to continue...")

    return


def dealer_play(hand, d_hand, deck):
    # how dealers hand plays out after players action is taken - returns BOOL: 0 if bust
    while d_hand.value < 17:
        d_hand.add_card(deck.draw_card())

        print("=" * 40)
        print("Dealer hits...")
        print("Dealer:", d_hand, sep="\n")
        print("Hand:", hand, sep="\n")

        if d_hand.is_bust():
            return False
        if d_hand.value < 17:
            input("Hit enter to continue...")

    return True


def check_winner(hand, d_hand, account, bet, split=0):
    # determine winner, assign payoff, return message (string)
    if hand.value > d_hand.value:
        calculate_payoff(bet, "win", account, hand, split)
        return "You win!\nHit Enter to return to Main Menu."
    if hand.value < d_hand.value:
        return "Dealer wins.\nHit Enter to return to Main Menu."
    if hand.value == d_hand.value:
        calculate_payoff(bet, "push", account, hand, split)
        return "Push!\nHit Enter to return to Main Menu."


def calculate_payoff(bet, outcome, account, hand, split=0):
    # calulate payoff based on action taken
    if outcome == "push":
        account.balance += bet
        account.net_earnings += bet
        return
    if outcome == "win":
        if hand.is_blackjack() and (not split):
            account.games_won += 1
            account.balance += round(2.5 * bet, 2)
            account.net_earnings += round(2.5 * bet, 2)
            return
        else:
            account.game_won(2 * bet)
            return


def main():
    # sets up user and account, then prompts user to main menu
    print(f"Hello! Welcome to the table. \n{'='*40}")
    user = User(input("Enter Name: "))
    account = Account(user)
    while True:  # this is not infinte as main menu will exit with sys.exit
        main_menu(account)


if __name__ == "__main__":
    main()
