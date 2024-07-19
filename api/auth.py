from passlib.context import CryptContext
from models import User as DBUser
from datetime import datetime, timedelta
import jwt






SECRET_KEY = "rrrr"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#создание токена
# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create JWT token
def create_access_token(data: dict):
    to_encode = data.copy()  # Убедитесь, что `data` является словарем
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

