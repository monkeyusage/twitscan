@echo off
python -m pip install -r requirements.txt
mkdir data
python twitscan\models.py