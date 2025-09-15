from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from cards import Base, Card
from EmbeddingGenerator import EmbeddingGenerator

class Database:
    def __init__(self, url="postgresql+psycopg2://postgres:root@localhost:5432/temporal_db"):
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        self.embedder = EmbeddingGenerator()

        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(self.engine)

    def add_card(self, title, content, metadata):
        embedding = self.embedder.generate_card_embedding(title, content)
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

    def vector_search(self, query_text, limit=5):
        query_embedding = self.embedder.generate_embedding(query_text)
        session = self.Session()
        try:
            return session.query(Card).order_by(
                Card.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
        finally:
            session.close()