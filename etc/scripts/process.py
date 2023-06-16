import arguably


@arguably.command
def process(*files):
    """
    process many files

    Args:
        files: the {file}s to process
    """
    for file in files:
        print(f"Processing {file}...")


if __name__ == "__main__":
    arguably.run()
