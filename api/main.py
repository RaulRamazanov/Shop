from fastapi import FastAPI, Depends, HTTPException, Request, Cookie, status, Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import Response
from database import SessionLocal, engine, Base
from models import User as DBUser, Item as DBItem, FavoriteItem, CartItem
from pydantic import BaseModel
from validation import User, UserCreate, Token, Item, ItemCreate, validate_user_create
from auth import *
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
    validated_user = validate_user_create(user_create.dict())  # Проводим валидацию данных пользователя
    if validated_user is None:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return {"detail": "Введены неверные данные пользователя"}

    user_id = str(uuid.uuid4())
    hashed_password = hash_password(validated_user.password)  # Используем валидированные данные
    db_user = DBUser(id=user_id, username=validated_user.username, email=validated_user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token({"user_id": user_id})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    print(access_token)
    return {"username": validated_user.username, "email": validated_user.email}



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    access_token = create_access_token({"sub": user.id})
    
    # Установка куки с токеном доступа и установка флага аутентификации вместе с ответом
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token)  # Устанавливаем токен в куку
    print(access_token)
    return response

@app.post("/logout/")
def logout(request: Request, response: Response, token: str = Cookie(None)):
    if token:
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print("Decoded Token:", decoded_token)
        except jwt.ExpiredSignatureError:
            # Токен устарел
            pass
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}


@app.delete("/users/{user_id}/")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return {"message": "User with ID {} has been deleted".format(user_id)}
    raise HTTPException(status_code=404, detail="User not found")

def has_token(request: Request) -> bool:
    access_token = request.cookies.get("access_token")
    return access_token is not None


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
async def profil(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    has_token = False
    user = None

    if access_token:
        has_token = True
        user_id = get_user_id_from_access_token(access_token)  # Получаем айди пользователя из токена
        user = db.query(DBUser).filter(DBUser.id == user_id).first()  # Получаем пользователя по айди из токена

    return templates.TemplateResponse("profil.html", {"request": request, "has_token": has_token, "user": user})