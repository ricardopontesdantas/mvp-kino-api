from collections.abc import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import Base

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / 'database'
DATABASE_FILE = DATABASE_DIR / 'db.sqlite3'
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f'sqlite:///{DATABASE_FILE}'

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
