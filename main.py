from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Request,status
from starlette.responses import FileResponse
from dbservice import Base,engine,SessionLocal,Product,Customer
from sqlalchemy.orm import Session
from schemas import ProductRequest,ProductResponse,CustomerResponse,CustomerCreate,Tags,LoginRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os,base64,tempfile
from pathlib import Path
from typing import Annotated
from passlib.context import CryptContext
from jwt import create_access_token,get_current_user
from fastapi.security import OAuth2PasswordRequestForm

app=FastAPI()

Base.metadata.create_all(bind=engine)


origins = [
    "http://localhost",
    "http://127.0.0.1:8000",
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/')
def index():
    return{"message": "welcome to FastAPI"}


# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/uploadfile" ,tags=[Tags.PRODUCT_IMAGE.value])
async def create_upload_image(file: UploadFile = File(...)):
    with open(f"./static/{file.filename}", "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename}


@app.post("/upload-image" , tags=[Tags.PRODUCT_IMAGE.value])
async def upload_image(image: UploadFile = File(...)):
    static_folder = "static"
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    # Read image contents
    image_contents = await image.read()

    # Encode image to Base64
    encoded_image = base64.b64encode(image_contents).decode("utf-8")

    # Save encoded image to static folder
    save_path = os.path.join(static_folder, image.filename + ".txt")  
    with open(save_path, "wb") as save_file:
        save_file.write(encoded_image.encode())

    return {"message": "Image uploaded and saved successfully"}

@app.get("/images_with_txt", tags=[Tags.PRODUCT_IMAGE.value])

async def get_all_images():
    static_folder = "static"
    image_files = os.listdir(static_folder)
    image_data = []

    for filename in image_files:
        if filename.endswith(".txt"):
            image_path = os.path.join(static_folder, filename)

            # Read Base64 encoded string from file
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            # Remove ".txt" extension from filename
            filename_without_extension = os.path.splitext(filename)[0]

            # Append filename (without extension) and encoded image data to the list
            image_data.append({"filename": filename_without_extension, "base64_data": encoded_string})

    return image_data
@app.get("/images" , tags=[Tags.PRODUCT_IMAGE.value])
async def get_images(request: Request):
    static_dir = Path("./static")

    try:
        image_files = [file for file in os.listdir(static_dir) if file.endswith(('.jpg', '.png', '.jpeg'))]
        base_url = str(request.base_url)
        image_urls = [f"{base_url.rstrip('/')}/images/{file}" for file in image_files]
        return image_urls

    except Exception as e:
      
        print(f"Error fetching images: {e}")
      
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
def fetch_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

# fetch by product id
@app.get('/products/{id}', response_model=ProductResponse ,tags=[Tags.PRODUCTS.value])
def fetch_single_products(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product does not exist")
    return product


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


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

@app.post('/login', tags=[Tags.LOGIN.value])
def login_user(login_details: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):

    user=db.query(Customer).filter(Customer.user_name==login_details.username).first()
    
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail =f"Invalid Credentials")
    if not verify_password(login_details.password, user.user_password):
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail =f"Invalid Credentials")

    
    access_token = create_access_token(data={"sub": user.user_name})
    return {"access_token":access_token, "token_type":"bearer"}
