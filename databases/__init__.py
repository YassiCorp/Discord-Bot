from sqlalchemy import create_engine
from libs.file_api import create_file
from libs.path import PATH_DB
import os

# ONLY DEV MODE
databasePath = f"{PATH_DB}/database.db"

def get_engine():
    if os.getenv("DEVMODE"):
        create_file(databasePath)
        return create_engine(f'sqlite:///{databasePath}', echo=False)
    else:
        return create_engine(f'mysql:///', echo=False)