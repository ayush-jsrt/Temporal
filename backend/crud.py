from sqlalchemy import create_engine, Column, Integer, Text, JSON, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

# Connect
engine = create_engine("postgresql+psycopg2://postgres:root@localhost:5432/temporal_db")
Base = declarative_base()

# Ensure pgvector extension exists
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

# Define table
class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    content = Column(Text)
    card_metadata = Column(JSON)
    embedding = Column(Vector(1536))
    created_at = Column(TIMESTAMP, server_default=func.now())

# Init DB
Base.metadata.create_all(engine)

# Session
Session = sessionmaker(bind=engine)
session = Session()

new_card = Card(
    title="AI Basics",
    content="Neural networks learn patterns...",
    card_metadata={"source": "notes"},
    embedding=[0.1] * 1536
)
session.add(new_card)
session.commit()
