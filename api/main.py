from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import Response
from database import SessionLocal, engine, Base
from models import User as DBUser, Item as DBItem, FavoriteItem, CartItem
from pydantic import BaseModel
from auth import pwd_context, hash_password, verify_password, create_access_token, get_user_by_email
import uuid

# подключение библиотеки
app = FastAPI()

# Подключаем папку с шаблонами(HTML)
templates = Jinja2Templates(directory="templates")

# Подключаем папку с статическими файлами (изображениями и css)
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Создание таблиц в базе данных(запуск engine)
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


# Создание пользователя(регистрация)
@app.post("/users/", response_model=User)
def create_user(response: Response, user_create: UserCreate, db: Session = Depends(get_db)):
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_create.password)  # Используйте bcrypt здесь
    db_user = DBUser(id=user_id, username=user_create.username, email=user_create.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Генерация JWT-токена для нового пользователя
    access_token = create_access_token({"user_id": user_id})
    
    # Установка куки с токеном
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    print(access_token)
    return {"username": user_create.username, "email": user_create.email}



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def has_token(request: Request) -> bool:
    access_token = request.cookies.get("access_token")
    return access_token is not None 


@app.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username)  # Изменено на form_data.email
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    access_token = create_access_token({"sub": user.id})
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout/")
def logout(response: Response):
    # Удаление куки 'access_token' путем установки времени истечения в прошлое
    response.delete_cookie("access_token")
    return RedirectResponse(url="/")

@app.delete("/users/{user_id}/")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return {"message": "User with ID {} has been deleted".format(user_id)}
    raise HTTPException(status_code=404, detail="User not found")




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

#гет запросы для фронтента

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "has_token": has_token(request)})

@app.get("/users/", response_class=HTMLResponse)
async def reg(request: Request):
    return templates.TemplateResponse("reg.html", {"request": request})


@app.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/profil/", response_class=HTMLResponse)
async def profil(request: Request):
    return templates.TemplateResponse("profil.html", {"request": request})

