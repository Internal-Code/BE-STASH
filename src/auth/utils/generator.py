import random
import string

def random_number(length: int=1) -> int:
    if length < 1:
        raise ValueError("length parameter should be more than 0")
    
    lower_bound = 10 ** (length - 1)
    upper_bound = 10 ** length - 1
    
    return random.randint(lower_bound, upper_bound)

def random_word(length: int=4) -> str:
    if length < 1:
        raise ValueError("length parameter should be more than 0")
    
    alphabet = string.ascii_lowercase
    word = ''.join(random.choice(alphabet) for _ in range(length))
    
    return word

def random_password(length: int=8) -> str:
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    special = ''.join(c for c in string.punctuation if c not in ['"', "'"])
    
    password = [
        random.choice(lower),
        random.choice(upper),
        random.choice(digits),
        random.choice(special),
    ]
    
    all_characters = lower + upper + digits + special
    password += random.choices(all_characters, k=length)
    
    random.shuffle(password)
    return ''.join(password)