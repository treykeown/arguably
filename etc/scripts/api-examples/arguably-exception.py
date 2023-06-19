#!/usr/bin/env python3
import arguably

@arguably.command
def example(collision_, _collision):
    print("You should never see this")

if __name__ == "__main__":
    arguably.run()
