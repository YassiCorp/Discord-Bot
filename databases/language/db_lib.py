from sqlalchemy import create_engine, Column, String, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from libs.file_api import create_file
from libs import path

databasePath = f"{path.PATH_DB}/database.db"
Base = declarative_base()

class ServerLanguage(Base):
    __tablename__ = 'lang.server_language'

    server_id = Column(Integer(), primary_key=True)
    lang_id = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

class UserLanguage(Base):
    __tablename__ = 'lang.user_language'

    user_id = Column(Integer(), primary_key=True)
    lang_id = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

class LanguageDB:
    def __init__(self):
        create_file(databasePath)
        self.engine = create_engine(f'sqlite:///{databasePath}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)()

    def has_default_language_guild(self, guild_id: int):
        return self.Session.query(ServerLanguage).filter_by(server_id=guild_id).first() is not None

    def has_default_language_user(self, user_id: int):
        return self.Session.query(UserLanguage).filter_by(user_id=user_id).first() is not None

    def get_default_language_guild(self, guild_id: int):
        result = self.Session.query(ServerLanguage).filter_by(server_id=guild_id).first()
        return result.lang_id if result else None

    def get_default_language_user(self, user_id: int):
        result = self.Session.query(UserLanguage).filter_by(user_id=user_id).first()
        return result.lang_id if result else None

    def set_default_language_guild(self, guild_id: int, lang_id: str):
        if self.has_default_language_guild(guild_id):
            self.Session.query(ServerLanguage).filter_by(server_id=guild_id).update({'lang_id': lang_id})
        else:
            self.Session.add(ServerLanguage(server_id=guild_id, lang_id=lang_id))

        self.Session.commit()

    def set_default_language_user(self, user_id: int, lang_id: str):
        if self.has_default_language_user(user_id):
            self.Session.query(UserLanguage).filter_by(user_id=user_id).update({'lang_id': lang_id})
        else:
            self.Session.add(UserLanguage(user_id=user_id, lang_id=lang_id))

        self.Session.commit()