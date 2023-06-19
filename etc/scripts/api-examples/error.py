#!/usr/bin/env python3
import arguably

@arguably.command
def high_five(*people):
    if len(people) > 5:
        arguably.error("Too many people to high-five!")
    for person in people:
        print(f"High five, {person}!")

if __name__ == "__main__":
    arguably.run()
