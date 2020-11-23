echo "Installing requirements for project"
pip install -r requirements.txt
echo "Creating data folder for database and other files"
mkdir data
echo "Creating database"
python twitscan\models.py