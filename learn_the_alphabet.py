import random


letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
score = [0, 0]


def reset_score():
    global score
    score = [0, 0]


def _redden_input(word1: str, word2: str):
    return input(f"\033[2K;1A;91m{word1}\033[0m for {word2}: ")


def letter_round():
    i = random.randrange(0, 26)
    guess = input(f"Letter for {i + 1}: ").strip()
    if guess.upper() == letters[i]:
        print("well done")
        return 1
    else:
        print(f"\033[91m{letters[i]}\033[0m")
        return 0


def number_round():
    i = random.randrange(0, 26)
    guess = input(f"Number for {letters[i]}: ").strip()
    if guess.isnumeric() and int(guess) == i + 1:
        print("well done")
        return 1
    else:
        print(f"\033[91m{i + 1}\033[0m")
        return 0


def mixed_round():
    if random.getrandbits(1):
        return letter_round()
    return number_round()


def _run(round_func):
    try:
        while True:
            score[0] += round_func()
            score[1] += 1
    except KeyboardInterrupt:
        s, t = score
        ratio = s / t if t > 0 else 0
        print(f"\ngg, {s}/{t} ({ratio:.1%})")


def main():
    option = input("Letters, numbers or both? (l/n/b): ")
    option = option.strip().lower() or "b"
    if option == "l":
        _run(letter_round)
    elif option == "n":
        _run(number_round)
    elif option == "b":
        _run(mixed_round)


if __name__ == "__main__":
    main()
