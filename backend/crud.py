from sqlalchemy import create_engine, Column, Integer, Text, JSON, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from cards import Base, Card

class Database:
    def __init__(self, url="postgresql+psycopg2://postgres:root@localhost:5432/temporal_db"):
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)

        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(self.engine)

    def add_card(self, title, content, metadata, embedding):
        session = self.Session()
        try:
            card = Card(
                title=title,
                content=content,
                card_metadata=metadata,
                embedding=embedding
            )
            session.add(card)
            session.commit()
            return card.id
        finally:
            session.close()

    def get_all_cards(self):
        session = self.Session()
        try:
            return session.query(Card).all()
        finally:
            session.close()