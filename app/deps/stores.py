
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.stores.sql_api_keys import SqlApiKeyStore

def get_api_key_store(db=Depends(get_db)):
    return SqlApiKeyStore(db)
