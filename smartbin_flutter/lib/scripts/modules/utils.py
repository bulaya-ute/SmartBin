import shlex

def split_command(command: str) -> list:
    return shlex.split(command)