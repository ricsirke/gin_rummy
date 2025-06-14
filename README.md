# Gin Rummy

This repository contains a minimal Python model of the card game Gin Rummy.

The `gin_rummy.py` script defines basic classes for cards, hands, players and the game itself. It includes a simple simulation that deals cards to two players and has them draw and discard randomly until someone goes gin or the deck runs out of cards.

Run the script with:

```bash
python3 gin_rummy.py
```

The example in `__main__` is purely demonstrative and does not implement full game strategy.

## Browser UI

You can also play against the random computer player through a very simple web
interface:

```bash
python3 web_ui.py
```

Open `http://localhost:8000` in a browser and follow the links to draw and
discard cards. The interface displays text representations of the cards.
