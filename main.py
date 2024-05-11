from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Request,status
from starlette.responses import FileResponse
from dbservice import Base,engine,SessionLocal,Product,Customer,Sale
from sqlalchemy.orm import Session
from schemas import ProductRequest,ProductResponse,CustomerResponse,CustomerCreate,Tags,\
LoginRequest,ImageResponse,SaleRequest,SaleResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os,base64,tempfile
from pathlib import Path
from typing import Annotated
from passlib.context import CryptContext
from jwt import create_access_token,get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse


 

app=FastAPI()

Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost",
    "http://localhost:5173"
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# connecting the application to the db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#test route
@app.get('/')
def index():
    return{"message": "welcome to FastAPI"}


# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
 

UPLOAD_DIRECTORY = "static/images"

# Create the directory if it doesn't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@app.post("/upload/", tags=[Tags.PRODUCT_IMAGE.value])
async def upload_image(file: UploadFile = File(...)):
    with open(os.path.join(UPLOAD_DIRECTORY, file.filename), "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename}

@app.get("/images" , tags=[Tags.PRODUCT_IMAGE.value])
async def get_images(request: Request):

    try:
        image_files = [file for file in os.listdir(UPLOAD_DIRECTORY) if file.endswith(('.jpg', '.png', '.jpeg'))]
        print("first........",image_files)
        base_url = str(request.base_url)
        print('second...........',base_url)
        image_urls = [f"{base_url.rstrip('/')}/images/{file}" for file in image_files]
        print('third.....l',image_urls)
        return image_urls

    except Exception as e:
      
        print(f"Error fetching images: {e}")
      
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/images/{filename}",tags=[Tags.PRODUCT_IMAGE.value])
async def get_image(filename: str):
    # Check if the image exists
    image_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Return the image file
    return StreamingResponse(open(image_path, "rb"), media_type="image/jpeg")


#Products...(post ,get and put)
@app.post('/products',tags=[Tags.PRODUCTS.value])
def add_products(product: ProductRequest, db: Session = Depends(get_db)):

    try:

        new_product = Product(
            product_name=product.product_name,
            product_quantity=product.product_quantity,
            product_price=product.product_price,
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except Exception as e:
        
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/products', response_model=list[ProductResponse], tags=[Tags.PRODUCTS.value])
def fetch_products(request: Request,db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        print("products.......",products)
        products_with_images = []
        for product in products:
            image_filename = f"product_{product.id}.jpg" 
            base_url = str(request.base_url)
            image_url =  f"{base_url.rstrip('/')}/images/{image_filename}"
            print("kwanzaaaaa ...............",image_url)
            products_with_images.append(ProductResponse(
                id=product.id,
                product_name=product.product_name,
                product_quantity=product.product_quantity,
                product_price=product.product_price,
                image_url=image_url
            ))
        return products_with_images
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# fetch by product id
@app.get('/products/{id}', response_model=ProductResponse ,tags=[Tags.PRODUCTS.value])
def fetch_single_products(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product does not exist")
    return product

@app.put('/purchase/{product_id}', tags=[Tags.PURCHASE.value])
def purchase_product(product_id: int, quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.product_quantity == 0:
        return {"message": "Product is out of stock"}

    if quantity > product.product_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    new_quantity = product.product_quantity - quantity
    if new_quantity == 0:
        product.product_quantity = new_quantity
        product.status = "out of stock"
    else:
        product.product_quantity = new_quantity

    db.commit()
    return {"message": "Purchase successful"},product
#sales get and post

@app.post('/sales')
def add_sale(sale: SaleRequest, db: Session = Depends(get_db)):
    try:
        new_sale=Sale(pid=sale.pid,quantity=sale.quantity,created_at=sale.created_at,user_id=sale.user_id)
        db.add(new_sale)
        db.commit()
        db.refresh(new_sale)
        return new_sale

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/sales',response_model= list[SaleResponse])
def fetch_sales(db: Session = Depends(get_db)):
    sales=db.query(Sale).all()
    return sales


#password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# customers....(post,get ,delete)
@app.post("/customers" ,tags=[Tags.CUSTOMERS.value])
async def create_customer(add_customer: CustomerCreate,  db: Session = Depends(get_db)):

    hashedpasword=pwd_context.hash(add_customer.user_password)

    db = SessionLocal()
    new_customer = Customer(
        user_name = add_customer.user_name,
        user_email = add_customer.user_email,
        user_password =hashedpasword,
        user_contact=add_customer.user_contact
        )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.get("/customers", response_model= list[CustomerResponse], tags=[Tags.CUSTOMERS.value])
def get_customer(db: Session = Depends(get_db),current_user: CustomerResponse = 
                 Depends(get_current_user)):
 
    registered_customer = db.query(Customer).all()
    if registered_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return registered_customer

@app.delete("/customers/{customer_id}", tags=[Tags.CUSTOMERS.value])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    registered_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not registered_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    try:
        db.delete(registered_customer)
        db.commit()
        return {"message": "Customer deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

#login
@app.post('/login', tags=[Tags.LOGIN.value])
def login_user(login_details: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):

    user=db.query(Customer).filter(Customer.user_name==login_details.username).first()
    
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail =f"Invalid Credentials")
    if not verify_password(login_details.password, user.user_password):
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail =f"Invalid Credentials")

    
    access_token = create_access_token(data={"sub": user.user_name})
    return {"access_token":access_token, "token_type":"bearer"}

# def dashboard(current_user: CustomerResponse = Depends(get_current_user), db: Session = Depends(get_db)):
#     customer = Customer.query.filter_by(user_name=current_user).first()
#     if not customer:
#         return {"message": "User not found"}, 404

#     sales_per_day = db.query(
#         func.date(Sale.created_at).label('date'),
#         # calculate the total number of sales per day
#         func.sum(Sale.quantity * Product.price).label('total_sales')
#     ).join(Product).group_by(
#         func.date(Sale.created_at)
#     ).all()

#     #  to JSON format
#     sales_data = [{'date': str(day), 'total_sales': sales}
#                   for day, sales in sales_per_day]
#     #  sales per product
#     sales_per_product = db.session.query(
#         Product.name,
#         func.sum(Sale.quantity*Product.price).label('sales_product')
#     ).join(Sale).group_by(
#         Product.name
#     ).all()

#     # to JSON format
#     salesproduct_data = [{'name': name, 'sales_product': sales_product}
#                          for name, sales_product in sales_per_product]

#     return jsonify({'sales_data': sales_data, 'salesproduct_data': salesproduct_data})
