import random
import string


class Generator:
    def random_number(self, length: int = 1) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0.")

        lower_bound = 10 ** (length - 1)
        upper_bound = 10**length - 1

        return str(random.randint(lower_bound, upper_bound))

    def random_word(self, length: int = 4) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0.")

        alphabet = string.ascii_lowercase
        word = "".join(random.choice(alphabet) for _ in range(length))

        return word
