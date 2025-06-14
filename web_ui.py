"""Flask based browser UI to play Gin Rummy against a random computer player."""

from flask import Flask, redirect, request, url_for

from gin_rummy import Player, GinRummyGame, Card, possible_melds
from random_player import RandomPlayer


app = Flask(__name__)

# Global game state
GAME: GinRummyGame | None = None
HUMAN: Player | None = None
COMPUTER: RandomPlayer | None = None
CURRENT_TURN = "human"
AWAITING_DISCARD = False
DECISION_PENDING = False  # waiting to knock or end turn


def start_new_game() -> None:
    """Create a fresh game and reset state variables."""
    global GAME, HUMAN, COMPUTER, CURRENT_TURN, AWAITING_DISCARD, DECISION_PENDING
    HUMAN = Player("You")
    COMPUTER = RandomPlayer("Computer")
    GAME = GinRummyGame([HUMAN, COMPUTER])
    CURRENT_TURN = "human"
    AWAITING_DISCARD = False
    DECISION_PENDING = False


def find_card(cards: list[Card], rep: str) -> Card | None:
    """Return the card from ``cards`` whose string representation matches ``rep``."""
    for c in cards:
        if str(c) == rep:
            return c
    return None


def is_valid_meld(cards: list[Card]) -> bool:
    """Return ``True`` if the given cards form a valid set or run."""
    if len(cards) < 3:
        return False
    ranks = {c.rank for c in cards}
    suits = {c.suit for c in cards}
    if len(ranks) == 1:
        return True
    if len(suits) == 1:
        sorted_ranks = sorted(c.rank for c in cards)
        return all(r == sorted_ranks[0] + i for i, r in enumerate(sorted_ranks))
    return False


def html_page(message: str = "") -> str:
    """Render the main game page as an HTML string."""
    assert GAME and HUMAN and COMPUTER
    top_discard = GAME.discard_pile[-1] if GAME.discard_pile else None
    hand = " ".join(c.to_html() for c in HUMAN.hand.cards)
    deck_count = len(GAME.deck.cards)

    html: list[str] = ["<html><body>"]
    html.append(f"<h2>Your hand: {hand}</h2>")
    if HUMAN.melds:
        for meld in HUMAN.melds:
            meld_str = " ".join(c.to_html() for c in meld)
            html.append(f"<p>Meld: {meld_str}</p>")
    if COMPUTER.melds:
        for meld in COMPUTER.melds:
            meld_str = " ".join(c.to_html() for c in meld)
            html.append(f"<p>Computer meld: {meld_str}</p>")
    td_display = top_discard.to_html() if top_discard else "None"
    html.append(f"<p>Top of discard pile: {td_display}</p>")
    html.append(f"<p>Cards left in deck: {deck_count}</p>")
    if message:
        html.append(f"<p>{message}</p>")

    if CURRENT_TURN == "human":
        html.append('<p><a href="/sort">Sort hand</a></p>')
        if AWAITING_DISCARD:
            html.append("<p>Select a card to discard:</p>")
            for card in HUMAN.hand.cards:
                html.append(f'<a href="/discard?card={card}">{card.to_html()}</a>')
        elif DECISION_PENDING:
            if HUMAN.hand.is_gin():
                html.append('<p><a href="/gin">Gin</a></p>')
            if HUMAN.hand.score_deadwood() <= 10:
                html.append('<p><a href="/knock">Knock</a></p>')
            html.append('<p><a href="/end_turn">End turn</a></p>')
        else:
            html.append("<p>Draw a card:</p>")
            html.append('<a href="/draw?source=deck">Deck</a> ')
            if GAME.discard_pile:
                html.append(f'<a href="/draw?source=discard">Discard ({top_discard.to_html()})</a>')
        melds = possible_melds(HUMAN.hand)
        if melds:
            html.append("<p>Lay down a meld:</p>")
            for meld in melds:
                label = " ".join(c.to_html() for c in meld)
                param = "-".join(str(c) for c in meld)
                html.append(f'<a href="/meld?cards={param}">{label}</a><br>')
    else:
        html.append("<p>Computer's turn...</p>")

    html.append('<p><a href="/reset">Restart</a></p>')
    html.append("</body></html>")
    return "\n".join(html)


def ensure_game() -> None:
    """Lazy-initialize the game if it hasn't been started yet."""
    if not all([GAME, HUMAN, COMPUTER]):
        start_new_game()


@app.route("/")
def index() -> str:
    global CURRENT_TURN
    ensure_game()

    # Computer plays automatically when it's its turn
    if CURRENT_TURN == "computer":
        assert COMPUTER and GAME
        COMPUTER.play_turn(GAME)
        if COMPUTER.hand.is_gin():
            return f"<p>Computer wins with hand: {COMPUTER.hand}</p>"
        CURRENT_TURN = "human"

    return html_page()


@app.route("/reset")
def reset() -> str:
    start_new_game()
    return redirect(url_for("index"))


@app.route("/sort")
def sort_hand() -> str:
    if CURRENT_TURN == "human" and HUMAN:
        HUMAN.hand.sort()
    return redirect(url_for("index"))


@app.route("/meld")
def meld() -> str:
    if CURRENT_TURN == "human" and HUMAN:
        card_param = request.args.get("cards", "")
        reps = [r for r in card_param.split("-") if r]
        cards = [find_card(HUMAN.hand.cards, r) for r in reps]
        if all(cards) and is_valid_meld(cards):
            for c in cards:
                HUMAN.hand.remove_card(c)
            HUMAN.melds.append(cards)
    return redirect(url_for("index"))


@app.route("/draw")
def draw() -> str:
    global AWAITING_DISCARD, DECISION_PENDING
    if CURRENT_TURN == "human" and not AWAITING_DISCARD and HUMAN and GAME:
        source = request.args.get("source", "deck")
        if source == "discard" and GAME.discard_pile:
            HUMAN.draw(GAME.discard_pile)
        else:
            HUMAN.draw(GAME.deck.cards)
        AWAITING_DISCARD = True
        DECISION_PENDING = False
    return redirect(url_for("index"))


@app.route("/discard")
def discard() -> str:
    global AWAITING_DISCARD, DECISION_PENDING
    if CURRENT_TURN == "human" and AWAITING_DISCARD and HUMAN and GAME:
        card_str = request.args.get("card", "")
        card = find_card(HUMAN.hand.cards, card_str)
        if card:
            HUMAN.discard(card, GAME.discard_pile)
            AWAITING_DISCARD = False
            if HUMAN.hand.is_gin():
                return f"<p>You win with hand: {HUMAN.hand}</p>"
            DECISION_PENDING = True
    return redirect(url_for("index"))


@app.route("/knock")
def knock() -> str:
    if CURRENT_TURN == "human" and DECISION_PENDING and HUMAN:
        if HUMAN.hand.score_deadwood() <= 10:
            return f"<p>You knock with hand: {HUMAN.hand}</p>"
    return redirect(url_for("index"))


@app.route("/gin")
def gin() -> str:
    if CURRENT_TURN == "human" and DECISION_PENDING and HUMAN:
        if HUMAN.hand.is_gin():
            return f"<p>You go gin with hand: {HUMAN.hand}</p>"
    return redirect(url_for("index"))


@app.route("/end_turn")
def end_turn() -> str:
    global CURRENT_TURN, DECISION_PENDING
    if CURRENT_TURN == "human" and DECISION_PENDING:
        DECISION_PENDING = False
        CURRENT_TURN = "computer"
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

