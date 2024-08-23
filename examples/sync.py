import time


def cook_noodle() -> str:
    print("prepare bowl and water")
    time.sleep(1)
    print("brew noodle")
    time.sleep(9)
    print("season the noodles")
    time.sleep(1)
    return "noodle served"


def eat() -> str:
    print("search chair")
    time.sleep(2)
    print("sit")
    time.sleep(1)
    print("eat noodle")
    time.sleep(1)
    return "wareg"


def main() -> str:
    start_time = time.time()
    cook_noodle()
    eat()
    end_time = time.time()
    elapsed_time = end_time - start_time
    return f"Execute time: {elapsed_time}"


print(main())
