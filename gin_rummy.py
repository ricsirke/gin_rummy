"""Simple Gin Rummy model."""

import random
from collections import defaultdict
from typing import List, Optional

class Card:
    SUITS = ['C', 'D', 'H', 'S']
    RANKS = list(range(1, 14))  # 1=Ace, 11=Jack, 12=Queen, 13=King

    def __init__(self, rank: int, suit: str):
        if rank not in Card.RANKS:
            raise ValueError('Invalid rank')
        if suit not in Card.SUITS:
            raise ValueError('Invalid suit')
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        names = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        r = names.get(self.rank, str(self.rank))
        return f'{r}{self.suit}'

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise RuntimeError('Deck is empty')
        return self.cards.pop()

class Hand:
    def __init__(self, cards: Optional[List[Card]] = None):
        self.cards: List[Card] = cards or []

    def add_card(self, card: Card):
        self.cards.append(card)

    def remove_card(self, card: Card):
        self.cards.remove(card)

    def sort(self):
        self.cards.sort(key=lambda c: (c.suit, c.rank))

    def __repr__(self):
        return ' '.join(map(str, self.cards))

    def score_deadwood(self) -> int:
        """Return the total pip value of unmatched cards."""
        _, deadwood = self._melds_and_deadwood()
        return sum(card.rank if card.rank <= 10 else 10 for card in deadwood)

    def is_gin(self) -> bool:
        melds, deadwood = self._melds_and_deadwood()
        return len(deadwood) == 0

    def _melds_and_deadwood(self):
        """Very naive meld detection: find sets first then runs."""
        remaining = list(self.cards)
        melds = []

        # find sets
        ranks = defaultdict(list)
        for card in remaining:
            ranks[card.rank].append(card)
        for cards in ranks.values():
            if len(cards) >= 3:
                melds.append(cards[:3])
                for c in cards[:3]:
                    remaining.remove(c)

        # find runs by suit
        suits = defaultdict(list)
        for card in remaining:
            suits[card.suit].append(card)
        for suit_cards in suits.values():
            suit_cards.sort(key=lambda c: c.rank)
            run = []
            last_rank = None
            for card in suit_cards:
                if last_rank is None or card.rank == last_rank + 1:
                    run.append(card)
                else:
                    if len(run) >= 3:
                        melds.append(run)
                        for c in run:
                            remaining.remove(c)
                    run = [card]
                last_rank = card.rank
            if len(run) >= 3:
                melds.append(run)
                for c in run:
                    if c in remaining:
                        remaining.remove(c)

        return melds, remaining

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()
        self.melds: List[List[Card]] = []  # cards the player has laid down

    def draw(self, source: List[Card]):
        card = source.pop()
        self.hand.add_card(card)
        return card

    def discard(self, card: Card, destination: List[Card]):
        self.hand.remove_card(card)
        destination.append(card)

class GinRummyGame:
    def __init__(self, players: List[Player]):
        if len(players) != 2:
            raise ValueError('Gin Rummy is typically played with two players')
        self.players = players
        self.deck = Deck()
        self.discard_pile: List[Card] = []

        # deal 10 cards each
        for _ in range(10):
            for p in self.players:
                p.hand.add_card(self.deck.draw())
        self.discard_pile.append(self.deck.draw())

    def play_round(self):
        current = 0
        while True:
            player = self.players[current]
            opponent = self.players[1 - current]

            if not self.deck.cards:
                # no cards left means the round ends in a draw
                return None

            if hasattr(player, "play_turn"):
                player.play_turn(self)
            else:
                # default random action
                drawn = self.deck.draw()
                player.hand.add_card(drawn)
                discard = random.choice(player.hand.cards)
                player.discard(discard, self.discard_pile)

            if player.hand.is_gin():
                return player

            current = 1 - current

        return None

if __name__ == '__main__':
    random.seed(42)
    from random_player import RandomPlayer

    players = [RandomPlayer('A'), RandomPlayer('B')]
    game = GinRummyGame(players)
    winner = game.play_round()
    if winner:
        print(f'{winner.name} wins with hand: {winner.hand}')
    else:
        print('Round ended in a draw.')
