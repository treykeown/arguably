import arguably

@arguably.command
def ec2__start_instances(*instances):
    """
    start instances
    Args:
        *instances: {instance}s to start
    """
    for inst in instances:
        print(f"Starting {inst}")

@arguably.command
def ec2__stop_instances(*instances):
    """
    stop instances
    Args:
        *instances: {instance}s to stop
    """
    for inst in instances:
        print(f"Stopping {inst}")

@arguably.command
def s3__ls(path="/"):
    """
    list objects
    Args:
        path: path to list under
    """
    print(f"Listing objects under {path}")

@arguably.command
def s3__cp(src, dst):
    """
    copy objects
    Args:
        src: source object
        dst: destination path
    """
    print(f"Copy {src} to {dst}")

if __name__ == "__main__":
    arguably.run()
