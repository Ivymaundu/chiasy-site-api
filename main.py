from fastapi import FastAPI,Depends,HTTPException,UploadFile,File
from dbservice import Base,engine,SessionLocal,Product,Customer
from sqlalchemy.orm import Session
from schemas import ProductRequest,ProductResponse,CustomerResponse,CustomerCreate
from fastapi.middleware.cors import CORSMiddleware
import os

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


UPLOAD_DIR = "static/products"

@app.post('/products')
def add_products(product: ProductRequest, file: UploadFile = File(...), db: Session = Depends(get_db)):

    try:

        with open(os.path.join(UPLOAD_DIR, file.filename), "wb") as buffer:
            buffer.write(file.file.read())
        

        new_product = Product(
            product_name=product.product_name,
            product_quantity=product.product_quantity,
            product_price=product.product_price,
            product_image = file.filename
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except Exception as e:
        
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/products', response_model=list[ProductResponse])
def fetch_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products
    

# @app.post("/customers/")
# def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    
    

@app.get("/customers", response_model=CustomerResponse)
def get_customer(db: Session = Depends(get_db)):
 
    customer = db.query(Customer).all()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer