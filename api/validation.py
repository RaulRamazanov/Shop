from pydantic import BaseModel, EmailStr, ValidationError

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    username: str
    email: EmailStr

class UserCreate(User):
    password: str

def validate_username(username: str):
    if not username.isalpha():
        raise ValueError('username должен содержать только буквы')
    if len(username) < 3:
        raise ValueError('username должен быть не короче 3 символов')

def validate_password(password: str):
    if not any(char.isdigit() for char in password):
        raise ValueError('пароль должен содержать минимум одну цифру')
    if not any(char.isalpha() for char in password):
        raise ValueError('пароль должен содержать минимум одну букву')
    if any(char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for char in password.lower()):
        raise ValueError('пароль не должен содержать русские буквы')
    if len(password) < 8:
        raise ValueError('пароль должен быть не короче 8 символов')

    # Вспомогательная функция для проверки валидации модели
def validate_user_create(user_data: dict):
    try:
        user = UserCreate(**user_data)
        validate_username(user.username)
        validate_password(user.password)
        return user
    except ValidationError as e:
        return None  # Возвращаем None если данные не прошли валидацию
    


class Item(BaseModel):
    title: str
    description: str
    price: int
    size: str
    color: str
    image_url: str


class ItemCreate(Item):
    pass