from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from database import SessionLocal, Order, Product
from pydantic import BaseModel

class Product(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    customer_id: int
    products: list[Product]



app = FastAPI()

@app.post("/orders/")
async def create_order(order: Order):
    with SessionLocal() as db:
        # Validar que los productos existen y hay suficiente stock
        for item in order.products:
            product_id = item.product_id
            quantity = item.quantity
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalars().first()
            if not product or product.stock < quantity:
                raise HTTPException(status_code=400, detail=f"Producto {product_id} no disponible o sin stock suficiente.")

        # Crear el pedido
        order = Order(customer_id=order.customer_id, created_at=datetime.utcnow())
        db.add(order)
        await db.commit()
        await db.refresh(order)

        # Actualizar el stock de los productos
        for item in product:
            product_id = item['product_id']
            quantity = item['quantity']
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalars().first()
            product.stock -= quantity  # Reducir el stock

        await db.commit()

        return {"order_id": order.id, "status": order.status, "created_at": order.created_at}

@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"order_id": order.id, "status": order.status}

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.status = status
        await db.commit()
        await db.refresh(order)
        return {"order_id": order.id, "status": order.status}

@app.get("/orders/")
async def list_orders(customer_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(Order).where(Order.customer_id == customer_id))
        orders = result.scalars().all()
        return [{"order_id": order.id, "status": order.status, "created_at": order.created_at} for order in orders]
