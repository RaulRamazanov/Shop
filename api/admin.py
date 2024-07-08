from fastapi import APIRouter

router = APIRouter()

@router.post("/products/")
async def create_product(product_name: str):
    # Здесь должна быть логика добавления товара в базу данных
    return {"message": f"Товар {product_name} успешно добавлен"}