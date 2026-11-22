from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from fastapi import Response
from typing import Literal
from fastapi import Query

app = FastAPI()

products = {
     82 : {"id" : 1, "name" : "Pen" , "price" : 5},
}

class Product(BaseModel):
    name : str
    price : int

class PriceUpdate(BaseModel):
    price : int


@app.patch("/products/{product_id}")
def update_price(product_id: int, update:PriceUpdate):
    product = products.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product["price"] = update.price
    return product

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@app.post("/products",status_code=201)
def add_product(product :Product):
    product_id = max(products,default = 0) + 1
    new_product = {
        "id": product_id,
        "name": product.name,
        "price":product.price,
    }
    products[product_id] = new_product
    return new_product

@app.delete("/products/{product_id}",status_code=204)
def delete_product(product_id: int):
    product = products.pop(product_id,None)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Response(status_code=204)


@app.get("/products")
def list_products(
    max_price: int,
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    matching_products = [
        product
        for product in products.values()
        if product["price"] <= max_price
    ]
    sorted_products = sorted(
        matching_products,
        key=lambda product: product["price"],
        reverse=(order == "desc"),
    )

    start = (page - 1) * limit
    return sorted_products[start : start + limit]