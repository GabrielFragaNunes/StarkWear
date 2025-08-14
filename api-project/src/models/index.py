from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ExampleModel(Base):
    __tablename__ = 'example'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# Database setup
DATABASE_URL = "sqlite:///example.db"  # Change this to your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)