import pytest
from random import randint
from examples.general import fizzbuzz


def generate_multiple_of_five_not_three():
    while True:
        num = randint(1, 20) * 5
        if num % 3 != 0:
            return num


multiple_three = randint(1, 4) * 3
multiple_only_five = generate_multiple_of_five_not_three()
multiple_only_five_and_three = randint(1, 4) * 15


@pytest.mark.asyncio
async def test_divide_number_only_multiple_of_three() -> str:
    """Should return fizz"""

    result = fizzbuzz(num=multiple_three)
    print(result)
    assert result == "fizz"


@pytest.mark.asyncio
async def test_divide_number_only_multiple_of_five() -> str:
    """Should return buzz"""

    result = fizzbuzz(num=multiple_only_five)
    print(result)
    assert result == "buzz"


@pytest.mark.asyncio
async def test_divide_number_only_multiple_of_five_and_three() -> str:
    """Should return fizzbuzz"""

    result = fizzbuzz(num=multiple_only_five_and_three)
    print(result)
    assert result == "fizzbuzz"
