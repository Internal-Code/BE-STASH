import time
import asyncio


async def cook_noodle() -> str:
    print("prepare bowl and water")
    await asyncio.sleep(1)
    print("brew noodle")
    await asyncio.sleep(9)
    print("season the noodles")
    await asyncio.sleep(1)
    return "noodle served"


async def eat() -> str:
    print("search chair")
    await asyncio.sleep(2)
    print("sit")
    await asyncio.sleep(15)
    print("eat noodle")
    await asyncio.sleep(1)
    return "wareg"


async def main() -> str:
    start_time = time.time()
    cooking = asyncio.create_task(cook_noodle())
    eating = asyncio.create_task(eat())
    await cooking
    await eating
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execute time: {elapsed_time}")


asyncio.run(main())
