import random
from gin_rummy import Player, possible_melds

class RandomPlayer(Player):
    """Player that makes random legal moves with no strategy."""

    def lay_down_melds(self):
        """Lay down all possible melds from the player's hand."""
        changed = True
        while changed:
            changed = False
            for meld in possible_melds(self.hand):
                if all(c in self.hand.cards for c in meld):
                    for c in meld:
                        self.hand.remove_card(c)
                    self.melds.append(meld)
                    changed = True
                    break

    def play_turn(self, game):
        """Perform a random legal turn in the given ``GinRummyGame``."""
        self.lay_down_melds()
        draw_from_discard = bool(game.discard_pile) and random.choice([True, False])
        if draw_from_discard:
            drawn = game.discard_pile.pop()
        else:
            drawn = game.deck.draw()
        self.hand.add_card(drawn)
        self.lay_down_melds()
        discard = random.choice(self.hand.cards)
        self.discard(discard, game.discard_pile)
