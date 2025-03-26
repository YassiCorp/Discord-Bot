from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import get_engine
import datetime

Base = declarative_base()

class BanTable(Base):
    __tablename__ = 'mod.ban'

    guild_id = Column(Integer(), nullable=False)
    user_id = Column(Integer(), primary_key=True)
    reason = Column(String(), nullable=True)
    duration = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

class KickTable(Base):
    __tablename__ = 'mod.kick'

    guild_id = Column(Integer(), nullable=False)
    user_id = Column(Integer(), primary_key=True)
    reason = Column(String(), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

class WarnTable(Base):
    __tablename__ = 'mod.warn'

    guild_id = Column(Integer(), nullable=False)
    user_id = Column(Integer(), primary_key=True)
    reason = Column(String(), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

class ModerationDB:
    def __init__(self):
        self.engine = get_engine()
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)()

    def add_ban(self, guild_id: int, user_id: int, reason: str = None, duration: datetime.datetime = None):
        self.Session.add(BanTable(guild_id=guild_id, user_id=user_id, reason=reason, duration=duration))
        self.Session.commit()

    def add_kick(self, guild_id: int, user_id: int, reason: str = None):
        self.Session.add(KickTable(guild_id=guild_id, user_id=user_id, reason=reason))
        self.Session.commit()

    def add_warn(self, guild_id: int, user_id: int, reason: str = None):
        self.Session.add(BanTable(guild_id=guild_id, user_id=user_id, reason=reason))
        self.Session.commit()

