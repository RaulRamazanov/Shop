
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User as DBUser, Item as DBItem, FavoriteItem, CartItem
from pydantic import BaseModel
import uuid

app = FastAPI()

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Переопределение SQLAlchemy моделей в Pydantic модели

class User(BaseModel):
    username: str
    email: str

class UserCreate(User):
    password: str

class Item(BaseModel):
    title: str
    description: str
    price: int
    size: str
    color: str
    image_url: str

class ItemCreate(Item):
    pass

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание пользователя
@app.post("/users/", response_model=User)
def create_user(user_create: UserCreate, db: Session = Depends(get_db)):
    user_id = str(uuid.uuid4())
    db_user = DBUser(id=user_id, username=user_create.username, email=user_create.email, password=user_create.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return user_create  # Return the Pydantic model here

# Создание товара
@app.post("/items/", response_model=Item)
def create_item(item_create: ItemCreate, db: Session = Depends(get_db)):
    item_id = str(uuid.uuid4())
    db_item = DBItem(id=item_id, **item_create.dict(), quantity=0)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return item_create  # Return the Pydantic model here

# Получение всех товаров
@app.get("/items/", response_model=list[Item])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(DBItem).offset(skip).limit(limit).all()
    return items