from fastapi import FastAPI, Depends, HTTPException, Request, Cookie, status, Path, Header,APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import Response
from database import SessionLocal, engine, Base
from models import User as DBUser, Item as DBItem, FavoriteItem, CartItem
from pydantic import BaseModel
from validation import User, UserCreate, Token, Item, ItemCreate, validate_user_create, UserUpdate, CartItemCreate
from typing import Optional
from auth import *
import uuid

# подключение библиотеки
app = FastAPI()

router = APIRouter()

# Подключаем папку с шаблонами(HTML)
templates = Jinja2Templates(directory="templates")

# Подключаем папку с статическими файлами (изображениями и css)
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Создание таблиц в базе данных(запуск engine)
Base.metadata.create_all(bind=engine)


# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Создание пользователя(регистрация)
@app.post("/users/", response_model=User, tags=['registration'])
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



#пут запрос для суперадмина(изменение роли)
@app.put("/users/{user_id}", response_model=UserUpdate, tags=['users'])
def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_data = user_update.dict(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


#гет запрос для суперадмина(только он может сюда перейти)
@app.get("/superadmin", response_class=HTMLResponse, tags=['users'])
def get_superadmin_page(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    current_user_id = None
    current_user_role = None

    if not access_token:
        raise HTTPException(status_code=401, detail="User is not authenticated")

    current_user_id = get_user_id_from_access_token(access_token)

    if not current_user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")

    current_user_role = get_user_role_by_id(db, current_user_id)

    if current_user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="You are not authorized to access this page")

    users = db.query(DBUser).all()  # Получаем всех пользователей из базы данных

    return templates.TemplateResponse("superadmin.html", {"request": request, "users": users})


#гет запрос для админа(только он может сюда перейти)
@app.get("/admin", response_class=HTMLResponse, tags=['users'])
def get_superadmin_page(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    current_user_id = None
    current_user_role = None

    if not access_token:
        raise HTTPException(status_code=401, detail="User is not authenticated")

    current_user_id = get_user_id_from_access_token(access_token)

    if not current_user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")

    current_user_role = get_user_role_by_id(db, current_user_id)

    if current_user_role != 'admin':
        raise HTTPException(status_code=403, detail="You are not authorized to access this page")

    users = db.query(DBUser).all()  # Получаем всех пользователей из базы данных

    return templates.TemplateResponse("admin.html", {"request": request, "users": users})

@app.post("/login/",  tags=['registration'])
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

@app.post("/logout/",  tags=['registration'])
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


@app.delete("/users/{user_id}/" , tags=['registration'])
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


#пост запрос для админа
@app.post("/items/", response_model=Item)
def create_item(item_create: ItemCreate, db: Session = Depends(get_db)):
    item_id = str(uuid.uuid4())
    db_item = DBItem(id=item_id, **item_create.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: str, item_update: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Получение всех товаров
@app.get("/items/", response_model=list[Item],  tags=['admin'])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(DBItem).offset(skip).limit(limit).all()
    return items


#удаление товара 
@app.delete("/items/{item_id}",  tags=['client'])
def delete_item(item_id: str, db: Session = Depends(get_db)):
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}




@app.post("/add-to-cart",  tags=['client'])
async def add_to_cart(cart_item: CartItemCreate, request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")  # проверка наличия токена

    user_id = get_user_id_from_access_token(access_token)  # Получаем айди пользователя из токена
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    # Создание экземпляра CartItem и сохранение его в базе данных
    new_cart_item = CartItem(user_id=user_id, item_id=cart_item.item_id, quantity=cart_item.quantity)
    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)

    return {"message": "Товар добавлен в корзину", "cart_item_id": new_cart_item.id}

#гет запросы для фронтента

@app.get("/", response_class=HTMLResponse, tags=['client'])
async def index(request: Request, skip: int = 0, limit: int = 40, db: Session = Depends(get_db)):
    items = db.query(DBItem).offset(skip).limit(limit).all()
    return templates.TemplateResponse("index.html", {"request": request, "items": items,  "has_token": has_token(request)})

@app.get("/cart", response_class=HTMLResponse, tags=['client'])
async def view_cart(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")  # проверка наличия токена

    user_id = get_user_id_from_access_token(access_token)  # Получаем айди пользователя из токена
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    # Запрос к базе данных для получения товаров в корзине по айди пользователя
    cart_items = db.query(CartItem).filter_by(user_id=user_id).all()

    # Возвращаем шаблон HTML с информацией о товарах в корзине
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items})


@app.delete("/cart/{item_id}" , tags=['client'])
async def remove_from_cart(item_id: str, request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")  # проверка наличия токена

    user_id = get_user_id_from_access_token(access_token)  # Получаем айди пользователя из токена
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    # Проверяем, есть ли такой товар в корзине
    cart_item = db.query(CartItem).filter_by(user_id=user_id, item_id=item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")

    # Удаляем товар из корзины
    db.delete(cart_item)
    db.commit()

    return {"message": "Товар успешно удален из корзины"}

@app.get("/users/", response_class=HTMLResponse, tags=['front(reg)'])
async def reg(request: Request):
    return templates.TemplateResponse("reg.html", {"request": request})


@app.get("/login/", response_class=HTMLResponse, tags=['front(reg)'])
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.get("/profil/", response_class=HTMLResponse, tags=['client'])
async def profil(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    has_token = False
    user = None

    if access_token:
        has_token = True
        user_id = get_user_id_from_access_token(access_token)  # Получаем айди пользователя из токена
        user = db.query(DBUser).filter(DBUser.id == user_id).first()  # Получаем пользователя по айди из токена

    return templates.TemplateResponse("profil.html", {"request": request, "has_token": has_token, "user": user})