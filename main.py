# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional, List
from datetime import datetime
from fastapi import Query

# DB config
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Modelos
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    stock: int

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    status: str = Field(default="Pendiente")
    created_at: datetime

from pydantic import BaseModel
# clase para recibir el pedido

class Item(BaseModel):
    product_id: int # IDs de productos que se va a comprar
    quantity: int   # cantidad que se va a comprar

class OrderCreate(BaseModel):
    customer_id: int
    products: List[Item]  # IDs de productos que se van a agregar

class Estado(BaseModel):
    status: str


# Crear tablas
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency para obtener sesión
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# Instancia de FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()

# 📦 PRODUCTOS

@app.post("/products/", response_model=Product)
async def create_product(product: Product, session: AsyncSession = Depends(get_session)):
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

@app.get("/products/", response_model=List[Product])
async def read_products(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Product))
    return result.all()

@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    await session.delete(product)
    await session.commit()
    return {"ok": True}

# 📦 PEDIDOS

@app.post("/orders/", response_model=Order)
async def create_order(order_data: OrderCreate, session: AsyncSession = Depends(get_session)):
    order = Order(
        customer_id=order_data.customer_id,
        created_at=datetime.utcnow()
    )

    for item in order_data.products:
        product_id = item.product_id
        quantity = item.quantity
        product = await session.get(Product, product_id)
        if not product or product.stock < quantity:
            raise HTTPException(status_code=400, detail=f"Producto {product_id} no disponible o sin stock suficiente.")
        
    session.add(order)
    await session.commit()
    await session.refresh(order)

    return order

@app.get("/orders/")
async def list_orders( customer_id: Optional[int] = Query(None), session: AsyncSession = Depends(get_session)):
    query = select(Order)
    if customer_id is not None:
        query = query.where(Order.customer_id == customer_id)

    result = await session.execute(query)
    orders = result.scalars().all()
    return orders


@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: int, session: AsyncSession = Depends(get_session)):
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order.id, "status": order.status}



@app.put("/orders/{order_id}/status")
async def update_order_status(nuevo_estado: Estado, order_id: int, session: AsyncSession = Depends(get_session)):
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.status = nuevo_estado.status
        await session.commit()
        await session.refresh(order)
        return {"order_id": order.id, "status": order.status}
 
# @app.post("/orders/")
# async def create_order(order: Order):
#     with SessionLocal() as db:
#         # Validar que los productos existen y hay suficiente stock
#         for item in order.products:
#             product_id = item.product_id
#             quantity = item.quantity
#             result = await db.execute(select(Product).where(Product.id == product_id))
#             product = result.scalars().first()
#             if not product or product.stock < quantity:
#                 raise HTTPException(status_code=400, detail=f"Producto {product_id} no disponible o sin stock suficiente.")

#         # Crear el pedido
#         order = Order(customer_id=order.customer_id, created_at=datetime.utcnow())
#         db.add(order)
#         await db.commit()
#         await db.refresh(order)

#         # Actualizar el stock de los productos
#         for item in product:
#             product_id = item['product_id']
#             quantity = item['quantity']
#             result = await db.execute(select(Product).where(Product.id == product_id))
#             product = result.scalars().first()
#             product.stock -= quantity  # Reducir el stock

#         await db.commit()

#         return {"order_id": order.id, "status": order.status, "created_at": order.created_at}

# @app.get("/orders/{order_id}/status")
# async def get_order_status(order_id: int):
#     async with SessionLocal() as db:
#         result = await db.execute(select(Order).where(Order.id == order_id))
#         order = result.scalars().first()
#         if not order:
#             raise HTTPException(status_code=404, detail="Order not found")
#         return {"order_id": order.id, "status": order.status}

# @app.put("/orders/{order_id}/status")
# async def update_order_status(order_id: int, status: str):
#     async with SessionLocal() as db:
#         result = await db.execute(select(Order).where(Order.id == order_id))
#         order = result.scalars().first()
#         if not order:
#             raise HTTPException(status_code=404, detail="Order not found")
#         order.status = status
#         await db.commit()
#         await db.refresh(order)
#         return {"order_id": order.id, "status": order.status}

# @app.get("/orders/")
# async def list_orders(customer_id: int):
#     async with SessionLocal() as db:
#         result = await db.execute(select(Order).where(Order.customer_id == customer_id))
#         orders = result.scalars().all()
#         return [{"order_id": order.id, "status": order.status, "created_at": order.created_at} for order in orders]
