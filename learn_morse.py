import random
from itertools import zip_longest
from time import time
from argparse import ArgumentParser


_values = [
    ".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---",
    "-.-", ".-..", "--", "-.", "---", ".--.", "--.-", ".-.", "...", "-", "..-",
    "...-", ".--", "-..-", "-.--", "--..", "-----", ".----", "..---", "...--",
    "....-", ".....", "-....", "--...", "---..", "----.", "/"
]

_keys = "abcdefghijklmnopqrstuvwxyz0123456789 "

CODES = dict(zip(_keys, _values))


def encode(chars: str):
    return " ".join(CODES.get(c, c) for c in chars.lower())


class _RandomLetters:
    letters = _keys[:-1]

    def get_random_word(self):
        return random.choice(self.letters)


class BaseGame:
    def __init__(self):
        self.score = self.rounds = 0

    def run(self):
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

        except (KeyboardInterrupt, StopIteration):
            self.on_game_end()

    def on_game_start(self):
        pass

    def get_word(self) -> str:
        raise NotImplementedError

    def write_prompt(self, word: str):
        raise NotImplementedError

    def check_guess(self, word: str, guess: str) -> bool:
        raise NotImplementedError

    def on_correct_guess(self, word: str, guess: str):
        pass

    def on_incorrect_guess(self, word: str, guess: str):
        pass

    def on_game_end(self):
        s, r = self.score, self.rounds
        print(f"\n{s}/{r} ({s / r:.2%})")  # e.g. 16/20 (80.00%)


class DecodeGame(BaseGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.randomizer = _RandomLetters()

    def get_word(self) -> str:
        return self.randomizer.get_random_word()

    def write_prompt(self, word: str):
        print("Decode:", encode(word))

    def check_guess(self, word: str, guess: str):
        return word == guess

    def on_correct_guess(self, word: str, guess: str):
        print(f"\033[1F\033[32m{guess} \033[0m")

    def on_incorrect_guess(self, word: str, guess: str):
        print(f"\033[31m{word}\033[0m")


class EncodeGame(BaseGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.randomizer = _RandomLetters()

    def get_word(self) -> str:
        return self.randomizer.get_random_word()

    def write_prompt(self, word: str):
        print("Encode:", word)

    def check_guess(self, word: str, guess: str):
        return encode(word) == " ".join(guess.split())

    def on_correct_guess(self, word: str, guess: str):
        print(f"\033[1F\033[32m{guess} \033[0m")

    def on_incorrect_guess(self, word: str, guess: str):
        truth = encode(word).split()
        for t, g in zip_longest(truth, guess.split(), fillvalue="x"):
            esc_code = "\033[32m" if t == g else "\033[31m"
            print(esc_code + t, end=" ")
        print("\033[0m")


class BlindEncodeGame(EncodeGame):
    def write_prompt(self, word: str):
        prompt = "Encode (press enter when ready): "
        input(f"{prompt}\033[34m{word}\033[0m ")
        print(f"\033[1F\033[0J{prompt}<hidden>")


class AlphabetGame(BaseGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iter_alphabet = (chr(i) for i in range(97, 123))

    def get_word(self) -> str:
        return next(self.iter_alphabet)

    def write_prompt(self, char: str):
        print("Encode:", char)

    def check_guess(self, char: str, guess: str):
        return encode(char) == guess

    def on_incorrect_guess(self, char: str, guess: str):
        print(f"\033[31m{encode(char)}\033[0m")


def timed_game(cls: type):
    class Timed(cls):
        def __init__(self, round_limit: int = 20, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.round_limit = round_limit
            self.start_time = None
            self.end_time = None

        def get_word(self):
            if self.rounds >= self.round_limit:
                raise StopIteration
            return super().get_word()

        def on_game_start(self):
            self.start_time = time()
            super().on_game_start()

        def on_game_end(self):
            end = self.end_time = time()
            start = self.start_time
            s, r = self.score, self.rounds
            print(f"\n{s}/{r} ({s / r:.2%}) in {end - start:0.2f}s")

    return Timed


def main(g: str = None, words: bool = False,
         timed: bool = False, blind: bool = False):

    games = {
        "e": EncodeGame, "d": DecodeGame,
        "a": AlphabetGame, "b": BlindEncodeGame
    }

    game = timed_game(games[g]) if timed else games[g]
    if g == "a":
        game().run()
    else:
        g = game()
        if words:
            # Large import (database). Only needed here.
            from random_word import RandomWords
            g.randomizer = RandomWords()
        g.run()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-g", "--game", default=None)
    parser.add_argument("-w", "--words", action="store_true")
    parser.add_argument("-e", "--encode", default=None)
    parser.add_argument("-d", "--decode", default=None)
    parser.add_argument("-t", "--timed", action="store_true")

    args = parser.parse_args()

    if args.encode is not None:
        print(encode(args.encode))
    elif args.decode is not None:
        decodes = {v: k for k, v in CODES.items()}
        print("".join(decodes[c] for c in args.decode.split()))
    else:
        main(args.game, args.words, args.timed)
