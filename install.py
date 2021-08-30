from os import system, name, path, mkdir

system("python -m venv venv")

cmd = r"venv\Scripts\activate" if name == "nt" else r"venv\bin\activate"
system(f"{cmd} && python -m pip install -r requirements.txt")

if not path.exists("data"):
    mkdir("data")
