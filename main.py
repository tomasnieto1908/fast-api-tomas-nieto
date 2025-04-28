from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from database import SessionLocal, Order, Product

app = FastAPI()

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/orders/")
async def create_order(customer_id: int, products: list, db: AsyncSession = Depends(get_db)):
    # Validar que los productos existen y hay suficiente stock
    for item in products:
        product_id = item['product_id']
        quantity = item['quantity']
        product = await db.execute(select(Product).where(Product.id == product_id))
        product = product.scalars().first()
        if not product or product.stock < quantity:
            raise HTTPException(status_code=400, detail=f"Producto {product_id} no disponible o sin stock suficiente.")

    # Crear el pedido
    order = Order(customer_id=customer_id, created_at=datetime.utcnow())
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Actualizar el stock de los productos
    for item in products:
        product_id = item['product_id']
        quantity = item['quantity']
        product = await db.execute(select(Product).where(Product.id == product_id))
        product = product.scalars().first()
        product.stock -= quantity  # Reducir el stock
        await db.commit()

    return {"order_id": order.id, "status": order.status, "created_at": order.created_at}

@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order.id, "status": order.status}

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    await db.commit()
    await db.refresh(order)
    return {"order_id": order.id, "status": order.status}

@app.get("/orders/")
async def list_orders(customer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.customer_id == customer_id))
    orders = result.scalars().all()
    return [{"order_id": order.id, "status": order.status, "created_at": order.created_at} for order in orders]
