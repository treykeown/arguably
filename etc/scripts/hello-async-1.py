import arguably
import asyncio

@arguably.command
async def hello(name):
    await asyncio.sleep(1)
    print(f"Hello, {name}!")

if __name__ == "__main__":
    arguably.run()
