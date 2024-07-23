from passlib.context import CryptContext
from models import User as DBUser
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError
from fastapi import Cookie, Request, HTTPException

SECRET_KEY = "rrrr"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create JWT token
def create_access_token(user_id: int):
    to_encode = {"user_id": user_id}  # Изменяем поле "sub" на "user_id"
    expiry = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Хеширование пароля с использованием bcrypt
def hash_password(password: str):
    return pwd_context.hash(password)

def get_user_by_email(db, email: str):
    user = db.query(DBUser).filter(DBUser.email == email).first()
    return user


def get_email_from_access_token(access_token: str) -> str:
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = decoded_token.get("email")  # Получаем email из токена
        print(email, decoded_token)
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    

def get_user_id_from_access_token(access_token: str) -> str:
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("user_id", {}).get("sub")  # Получаем айди пользователя из токена
        print(user_id)
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")