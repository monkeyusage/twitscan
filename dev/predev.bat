python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
mkdir data
python twitscan\models.py