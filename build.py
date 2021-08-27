from os import system

cmds = [
    "isort twitscan",
    "black .",
    "mypy twitscan --strict --ignore-missing-imports",
    "pytest tests",
    "pylint twitscan",
]

for cmd in cmds:
    system(f"python -m {cmd}")
