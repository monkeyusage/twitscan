from os import system

cmds = [
    "black .",
    "isort twitscan",
    "mypy twitscan --strict --ignore-missing-imports",
    "pytest tests",
]

for cmd in cmds:
    system(f"python -m {cmd}")
