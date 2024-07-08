from sqlalchemy import Column, Integer, String
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

# Модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default='client')  # Роль пользователя, по умолчанию 'client'

    # Один ко многим: пользователь может иметь много товаров в избранном и корзине
    favorites = relationship("FavoriteItem", back_populates="user")
    cart = relationship("CartItem", back_populates="user")

# Модель товара
class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer)
    size = Column(String)  
    color = Column(String)  
    image_url = Column(String)  # URL для изображения товара

# Модель товара в избранном пользователя
class FavoriteItem(Base):
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_id = Column(Integer, ForeignKey('items.id'))

    user = relationship("User", back_populates="favorites")
    item = relationship("Item")

# Модель товара в корзине пользователя
class CartItem(Base):
    __tablename__ = 'cart'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart")
    item = relationship("Item")