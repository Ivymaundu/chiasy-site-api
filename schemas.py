from pydantic import BaseModel


class ProductRequest(BaseModel):
    product_name: str
    product_price: float
    product_quantity: int



class ProductResponse(BaseModel):
    id: int
    product_name: str
    product_price: float
    product_quantity: int
    

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

    class Config:
        orm_mode = True

