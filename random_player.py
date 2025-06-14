import random
from gin_rummy import Player

class RandomPlayer(Player):
    """Player that makes random legal moves with no strategy."""

    def play_turn(self, game):
        """Perform a random legal turn in the given ``GinRummyGame``."""
        draw_from_discard = bool(game.discard_pile) and random.choice([True, False])
        if draw_from_discard:
            drawn = game.discard_pile.pop()
            self.hand.add_card(drawn)
            discard_options = [c for c in self.hand.cards if c is not drawn]
        else:
            drawn = game.deck.draw()
            self.hand.add_card(drawn)
            discard_options = self.hand.cards

        discard = random.choice(discard_options)
        self.discard(discard, game.discard_pile)
