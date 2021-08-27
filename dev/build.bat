@echo off
black .
mypy run.py --ignore-missing-imports
python -m pytest tests