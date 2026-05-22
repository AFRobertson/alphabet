# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "random-word>=1.0.13",
# ]
# ///

import sys
from enum import StrEnum
from abc import ABC, abstractmethod
import random
from itertools import zip_longest
from time import time
from argparse import ArgumentParser
from typing import Callable


_values = (
    ".- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- "
    ".--. --.- .-. ... - ..- ...- .-- -..- -.-- --.. ----- .---- "
    "..--- ...-- ....- ..... -.... --... ---.. ----. /"
).split()

_keys = "abcdefghijklmnopqrstuvwxyz0123456789 "

CODES = dict(zip(_keys, _values))


def encode(chars: str):
    return " ".join(CODES.get(c, c) for c in chars.lower())


def decode(morse: str):
    decodes = {v: k for k, v in CODES.items()}
    return "".join(decodes[c] for c in morse.split())


def encode_binary(chars: str):
    return " ".join(f"{ord(c):b}" for c in chars)


def decode_binary(code: str):
    return "".join(chr(int(n, base=2)) for n in code.split())


def decode_hex(code: str):
    return "".join(chr(int(n, base=16)) for n in code.split())


def encode_hex(chars: str):
    return " ".join(f"{ord(c):x}" for c in chars)


class _RandomLetters:
    letters = _keys[:-1]

    def get_random_word(self):
        return random.choice(self.letters)


class BaseGame(ABC):
    """Abstract base class for Morse code games."""

    _registry = {}

    def __init__(self, **_):
        self.score = self.rounds = 0
        self.encode = encode

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._registry[cls.__name__] = cls

    @classmethod
    def game_registry(cls) -> dict['BaseGame']:
        """Returns a dictionary of games subclassing `BaseGame`."""
        return cls._registry.copy()

    # Implements the game loop logic with hooks for game events.
    def run(self):
        """Runs the game loop."""
        self.on_game_start()
        try:
            while True:
                word = self.get_word()
                self.write_prompt(word)
                guess = input()
                self.rounds += 1

                if self.check_guess(word, guess):
                    self.score += 1
                    self.on_correct_guess(word, guess)
                else:
                    self.on_incorrect_guess(word, guess)

        except (KeyboardInterrupt, StopIteration, EOFError):
            self.on_game_end()

    def on_game_start(self):
        """Hook for actions occuring before the game starts."""
        pass

    @abstractmethod
    def get_word(self) -> str:
        """Returns a word or character to be guessed."""
        raise NotImplementedError

    @abstractmethod
    def write_prompt(self, word: str):
        """Writes the prompt to the console with the word to guess."""
        raise NotImplementedError

    @abstractmethod
    def check_guess(self, word: str, guess: str) -> bool:
        """Checks if the guess is correct."""
        raise NotImplementedError

    def on_correct_guess(self, word: str, guess: str):
        """Hook for actions after a correct guess."""
        pass

    def on_incorrect_guess(self, word: str, guess: str):
        """Hook for actions after an incorrect guess."""
        pass

    def on_game_end(self):
        """Hook for actions occuring after the game ends."""
        s, r = self.score, self.rounds
        r = r or 1
        print(f"\n{s}/{r} ({s / r:.2%})")  # e.g. 16/20 (80.00%)


class DecodeGame(BaseGame):
    """Game for decoding Morse code into English text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.randomizer = _RandomLetters()

    def get_word(self) -> str:
        return self.randomizer.get_random_word()

    def write_prompt(self, word: str):
        print("Decode:", self.encode(word))

    def check_guess(self, word: str, guess: str):
        return word == guess

    def on_correct_guess(self, word: str, guess: str):
        print(f"\033[1F\033[32m{guess} \033[0m")

    def on_incorrect_guess(self, word: str, guess: str):
        print(f"\033[31m{word}\033[0m")


class EncodeGame(BaseGame):
    """Game for translating random words or letters into Morse code."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.randomizer = _RandomLetters()

    def get_word(self) -> str:
        return self.randomizer.get_random_word()

    def write_prompt(self, word: str):
        print("Encode:", word)

    def check_guess(self, word: str, guess: str):
        return self.encode(word) == " ".join(guess.split())

    def on_correct_guess(self, word: str, guess: str):
        print(f"\033[1F\033[32m{guess} \033[0m")

    def on_incorrect_guess(self, word: str, guess: str):
        truth = self.encode(word).split()
        for t, g in zip_longest(truth, guess.split(), fillvalue="x"):
            esc_code = "\033[32m" if t == g else "\033[31m"
            print(esc_code + t, end=" ")
        print("\033[0m")


class BlindEncodeGame(EncodeGame):
    """Game for encoding words without seeing them. (Hard)"""

    def write_prompt(self, word: str):
        prompt = "Encode (press enter when ready): "
        input(f"{prompt}\033[36m{word}\033[0m ")  # Prints the word in blue.
        print(f"\033[1F\033[0J{prompt}<hidden>")  # Hides the word.


class AlphabetGame(BaseGame):
    """Tutorial game for learning the Morse code alphabet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iter_alphabet = (chr(i) for i in range(97, 123))
        self.round_limit = 26  # Runs full alphabet in timed games.

    def get_word(self) -> str:
        return next(self.iter_alphabet)

    def write_prompt(self, char: str):
        print("Encode:", char)

    def check_guess(self, char: str, guess: str):
        return self.encode(char) == guess

    def on_incorrect_guess(self, char: str, guess: str):
        print(f"\033[31m{self.encode(char)}\033[0m")


class TimedMixin:
    """Mixin for adding a timer and round limit to games."""

    def __init__(self, round_limit: int = 20, *args, **kwargs):
        self.round_limit = round_limit
        self.start_time = None
        self.end_time = None
        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__doc__ = cls.__mro__[2].__doc__ + " [TIMED]"

    def get_word(self):
        if self.rounds >= self.round_limit:
            raise StopIteration
        return super().get_word()

    def on_game_start(self):
        self.start_time = time()
        return super().on_game_start()

    def on_game_end(self):
        end = self.end_time = time()
        start = self.start_time
        s, r = self.score, self.rounds
        print(f"\n{s}/{r} ({s / r:.2%}) in {end - start:0.2f}s")


class TimedDecodeGame(TimedMixin, DecodeGame):
    pass

class TimedEncodeGame(TimedMixin, EncodeGame):
    pass

class TimedBlindEncodeGame(TimedMixin, BlindEncodeGame):
    pass

class TimedAlphabetGame(TimedMixin, AlphabetGame):
    pass


class Game(StrEnum):
    DECODE = "DecodeGame"
    ENCODE = "EncodeGame"
    BLIND = "BlindEncodeGame"
    ALPHABET = "AlphabetGame"

    def create(
        self,
        timed: bool = False,
        binary: bool = False,
        hexadecimal: bool = False,
        *args,
        **kwargs
    ):
        """Creates an instance of the game."""

        binary = binary and not hexadecimal

        class_name = "Timed" * timed + self.value
        game: BaseGame = BaseGame.game_registry()[class_name](*args, **kwargs)

        if binary:
            game.set_encode(encode_binary)
        if hexadecimal:
            game.set_encode(encode_hex)

        return game


def main(
    game: str,
    wordgame: bool = False,
    timed: bool = False,
    rounds: int = 20,
    binary: bool = False,
    hexadecimal: bool = False,
):

    game_name = game.upper()
    try:
        game = Game[game_name].create(
            timed,
            binary,
            hexadecimal,
            round_limit=rounds,
        )
    except KeyError:
        print(f"Unknown game: {game_name}")
        return 1

    if wordgame and not game_name.endswith("ALPHABET"):
        # Large database import; only needed here.
        from random_word import RandomWords
        game.randomizer = RandomWords()

    game.run()


if __name__ == "__main__":

    parser = ArgumentParser(
        description="Games to teach Morse code. End untimed games with Ctrl+C."
    )
    parser.add_argument("-g", "--game", default="DECODE",
                        help="game to play: DECODE, ENCODE, BLIND or ALPHABET")
    parser.add_argument("-w", "--wordgame", action="store_true",
                        help="generate random words instead of letters")
    parser.add_argument("-t", "--timed", action="store_true",
                        help="play a timed game")
    parser.add_argument("-r", "--rounds", type=int, default=20,
                        help="number of rounds in a timed game")
    parser.add_argument("-p", "--translate",
                        help="encode or decode the given text or Morse code")
    parser.add_argument("-b", "--binary", action="store_true",
                        help="encode letters to binary instead of Morse")
    parser.add_argument("-x", "--hex", action="store_true",
                        help="encode letters to hexadecimal instead of Morse")

    args = parser.parse_args()

    if (t := args.translate) is not None:
        if all(m in _values for m in t.split()):
            sys.exit(print(decode(t)))
        else:
            sys.exit(print(encode(t)))

    else:
        sys.exit(main(
            args.game,
            args.wordgame,
            args.timed,
            args.rounds,
            args.binary,
            args.hex,
        ))
