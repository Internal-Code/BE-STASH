import random


def random_number(length: int = 1) -> str:
    if length < 1:
        raise ValueError("length parameter should be more than 0.")

    lower_bound = 10 ** (length - 1)
    upper_bound = 10**length - 1

    return str(random.randint(lower_bound, upper_bound))
