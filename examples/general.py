import random

random_number = random.randrange(1, 101)


def fizzbuzz(num: int) -> str | int:
    if num % 5 == 0 and num % 3 == 0:
        return "fizzbuzz"
    if num % 5 == 0:
        return "buzz"

    if num % 3 == 0:
        return "fizz"

    return num


print(f"random num: {15}")
print(f"result: {fizzbuzz(num=15)}")
