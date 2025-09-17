from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from cards import Base, Card
from ai_service import AIService

class Database:
    def __init__(self, url="postgresql+psycopg2://postgres:root@localhost:5432/temporal_db"):
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        self.ai_service = AIService()

        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(self.engine)

    def add_card(self, title, content, metadata):
        embedding = self.ai_service.generate_embedding(content)
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
        query_embedding = self.ai_service.generate_embedding(query_text)
        session = self.Session()
        try:
            return session.query(Card).order_by(
                Card.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
        finally:
            session.close()

    def delete_card(self, card_id):
        session = self.Session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card:
                session.delete(card)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_card_by_id(self, card_id):
        session = self.Session()
        try:
            return session.query(Card).filter(Card.id == card_id).first()
        finally:
            session.close()

    def update_card(self, card_id, title=None, content=None, metadata=None):
        """Update a card's title, content, and/or metadata. Updates embedding if content changes."""
        session = self.Session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return None
            
            # Update fields if provided
            if title is not None:
                card.title = title
            if content is not None:
                card.content = content
                # Generate new embedding when content changes
                card.embedding = self.ai_service.generate_embedding(content)
            if metadata is not None:
                card.card_metadata = metadata
            
            session.commit()
            
            # Refresh the object to get latest data and make it accessible after session close
            session.refresh(card)
            
            # Create a detached copy with all the data we need
            updated_card = Card(
                title=card.title,
                content=card.content,
                card_metadata=card.card_metadata,
                embedding=card.embedding
            )
            updated_card.id = card.id
            updated_card.created_at = card.created_at
            
            return updated_card
        finally:
            session.close()