from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid

# Модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default='client')

    favorites = relationship("FavoriteItem", back_populates="user")
    cart = relationship("CartItem", back_populates="user")
    sales = relationship("Sale", back_populates="buyer")

# Модель товара
class Item(Base):
    __tablename__ = 'items'

    id = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    title = Column(String, index=True)
    pol = Column(String, index=True)
    types = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer)
    size = Column(String)
    color = Column(String)
    image_url = Column(String)
    quantity = Column(Integer, default=0)

    favorites = relationship("FavoriteItem", back_populates="item")
    cart = relationship("CartItem", back_populates="item")
    sales = relationship("Sale", back_populates="item")

# Модель товара в избранном пользователя
class FavoriteItem(Base):
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    item_id = Column(String, ForeignKey('items.id'))

    user = relationship("User", back_populates="favorites")
    item = relationship("Item", back_populates="favorites")

# Модель товара в корзине пользователя
class CartItem(Base):
    __tablename__ = 'cart'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    item_id = Column(String, ForeignKey('items.id'))
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart")
    item = relationship("Item", back_populates="cart")

# Модель продаж
class Sale(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    item_id = Column(String, ForeignKey('items.id'))
    quantity = Column(Integer)
    total_amount = Column(Integer)

    buyer = relationship("User", back_populates="sales")
    item = relationship("Item", back_populates="sales")
