from sqlmodel import SQLModel, Field, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from typing import Optional
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./test.db"  # Cambia a PostgreSQL si es necesario

# Crear el motor de la base de datos
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = Session  # Usado con AsyncSession más adelante si lo necesitás

# Definición del modelo de Producto
class Product(SQLModel, table=True):
    __tablename__ = "products"    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    stock: int

# Definición del modelo de Pedido
class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    status: str = Field(default="Pendiente")
    created_at: datetime