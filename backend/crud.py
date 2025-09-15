from sqlalchemy import create_engine, Column, Integer, Text, JSON, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    content = Column(Text)
    card_metadata = Column(JSON)
    embedding = Column(Vector(1536))
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, created_at={self.created_at})>"

class Database:
    def __init__(self, url="postgresql+psycopg2://postgres:root@localhost:5432/temporal_db"):
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)

        # ensure extension + tables
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

#usage example

if __name__ == "__main__":
    db = Database()
    card_id = db.add_card(
        title="Sample Card",
        content="This is a sample card content.",
        metadata={"author": "John Doe", "tags": ["sample", "test"]},
        embedding=[0.1] * 1536  # Example embedding vector
    )
    print(f"Added card with ID: {card_id}")

    cards = db.get_all_cards()
    for card in cards:
        print(f"Card ID: {card.id}, Title: {card.title}, Created At: {card.created_at}")