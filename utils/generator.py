import random
import string


class Generator:
    @staticmethod
    def random_number(length: int = 1) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0")

        lower_bound = 10 ** (length - 1)
        upper_bound = 10**length - 1

        return str(random.randint(lower_bound, upper_bound))

    @staticmethod
    def random_word(length: int = 4) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0")

        alphabet = string.ascii_lowercase
        word = "".join(random.choice(alphabet) for _ in range(length))

        return word
