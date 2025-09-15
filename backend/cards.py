from sqlalchemy import Column, Integer, Text, JSON, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    content = Column(Text)
    card_metadata = Column(JSON)
    embedding = Column(Vector(1024))
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, created_at={self.created_at})>"
