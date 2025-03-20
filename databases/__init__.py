import os
from sqlalchemy import create_engine
from config import path
from libs.file_api import create_file

# ONLY DEV MODE
databasePath = f"{path.PATH_DB}/database.db"

def get_engine():
    if os.getenv("DEVMODE"):
        create_file(databasePath)
        return create_engine(f'sqlite:///{databasePath}', echo=False)
    else:
        return create_engine(f'mysql:///', echo=False)