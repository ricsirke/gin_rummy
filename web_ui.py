"""Minimal browser UI to play Gin Rummy against a random computer player."""

from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

from gin_rummy import Player, GinRummyGame
from random_player import RandomPlayer

# Global game state
GAME = None
HUMAN = None
COMPUTER = None
CURRENT_TURN = "human"
AWAITING_DISCARD = False


def start_new_game():
    global GAME, HUMAN, COMPUTER, CURRENT_TURN, AWAITING_DISCARD
    HUMAN = Player("You")
    COMPUTER = RandomPlayer("Computer")
    GAME = GinRummyGame([HUMAN, COMPUTER])
    CURRENT_TURN = "human"
    AWAITING_DISCARD = False


def find_card(cards, rep):
    for c in cards:
        if str(c) == rep:
            return c
    return None


def redirect(start_response, location="/"):
    start_response("303 See Other", [("Location", location)])
    return [b""]


def html_page(message=""):
    top_discard = GAME.discard_pile[-1] if GAME.discard_pile else "None"
    hand = " ".join(str(c) for c in HUMAN.hand.cards)
    deck_count = len(GAME.deck.cards)

    html = ["<html><body>"]
    html.append(f"<h2>Your hand: {hand}</h2>")
    html.append(f"<p>Top of discard pile: {top_discard}</p>")
    html.append(f"<p>Cards left in deck: {deck_count}</p>")
    if message:
        html.append(f"<p>{message}</p>")

    if CURRENT_TURN == "human":
        if AWAITING_DISCARD:
            html.append("<p>Select a card to discard:</p>")
            for card in HUMAN.hand.cards:
                html.append(f'<a href="/discard?card={card}">{card}</a> ')
        else:
            html.append("<p>Draw a card:</p>")
            html.append('<a href="/draw?source=deck">Deck</a> ')
            if GAME.discard_pile:
                html.append(f'<a href="/draw?source=discard">Discard ({top_discard})</a>')
    else:
        html.append("<p>Computer's turn...</p>")

    html.append('<p><a href="/reset">Restart</a></p>')
    html.append("</body></html>")
    return "".join(html).encode()


def application(environ, start_response):
    global CURRENT_TURN, AWAITING_DISCARD
    if not any([GAME, HUMAN, COMPUTER]):
        start_new_game()

    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/reset":
        start_new_game()
        return redirect(start_response)

    if path == "/draw" and CURRENT_TURN == "human" and not AWAITING_DISCARD:
        source = query.get("source", ["deck"])[0]
        if source == "discard" and GAME.discard_pile:
            HUMAN.draw(GAME.discard_pile)
        else:
            HUMAN.draw(GAME.deck.cards)
        AWAITING_DISCARD = True
        return redirect(start_response)

    if path == "/discard" and CURRENT_TURN == "human" and AWAITING_DISCARD:
        card_str = query.get("card", [""])[0]
        card = find_card(HUMAN.hand.cards, card_str)
        if card:
            HUMAN.discard(card, GAME.discard_pile)
            AWAITING_DISCARD = False
            if HUMAN.hand.is_gin():
                start_response("200 OK", [("Content-Type", "text/html")])
                return [f"<p>You win with hand: {HUMAN.hand}</p>".encode()]
            CURRENT_TURN = "computer"
        return redirect(start_response)

    # Computer's turn if applicable
    if CURRENT_TURN == "computer":
        COMPUTER.play_turn(GAME)
        if COMPUTER.hand.is_gin():
            start_response("200 OK", [("Content-Type", "text/html")])
            return [f"<p>Computer wins with hand: {COMPUTER.hand}</p>".encode()]
        CURRENT_TURN = "human"

    start_response("200 OK", [("Content-Type", "text/html")])
    return [html_page()]


if __name__ == "__main__":
    with make_server("", 8000, application) as httpd:
        print("Serving on port 8000...")
        httpd.serve_forever()
