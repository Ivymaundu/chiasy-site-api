from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime

class Tags(Enum):
    PRODUCTS = "Products"
    CUSTOMERS = "Customers"
    PRODUCT_IMAGE ="product_image"
    LOGIN="login"
    PURCHASE="purchase"

class ProductRequest(BaseModel):
    product_name: str
    product_price: float
    product_quantity: int



class ProductResponse(BaseModel):
    id: int
    product_name: str
    product_price: float
    product_quantity: int
    image_url: str
    
class SaleRequest(BaseModel):
    pid: int
    quantity: int
    created_at: Optional[datetime]
    customer_id: int

class SaleResponse(SaleRequest):
    id: int
    

class CustomerCreate(BaseModel):
    user_name: str
    user_password: str
    user_email: str
    user_contact: str

class CustomerResponse(BaseModel):
    id: int
    user_name: str
    user_email: str
    user_contact: str

class LoginRequest(BaseModel):
    user_name : str
    user_password : str

class TokenData(BaseModel):
    username: Optional[str] =  None


class ImageResponse(BaseModel):
    filename: str
    content_type: str