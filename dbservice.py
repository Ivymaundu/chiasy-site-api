from sqlalchemy import create_engine,Column,Integer,String,ForeignKey,Float,DateTime
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


#connecting to the database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345@localhost/chiasy-db"

engine= create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



class Product(Base):
    __tablename__= 'products'

    id=Column(Integer,primary_key=True,autoincrement=True)
    product_name=Column(String(100),nullable=False)
    product_quantity=Column(Integer,nullable=False)
    product_price=Column(Float,nullable=False)

    #relationship with order items
    order_items = relationship('OrderItem', backref='product')


class Customer(Base):
    __tablename__="customers"

    id=Column(Integer,primary_key=True,autoincrement=True)
    user_name=Column(String(100),nullable=False)
    user_password=Column(String(255),nullable=False)
    user_email=Column(String(100),nullable=False)
    user_contact=Column(String(15),nullable=False)

    #relationship with orders
    orders = relationship('Order', backref='customer')
    

class Order(Base):
    __tablename__="orders"

    id=Column(Integer,primary_key=True,autoincrement=True)
    order_number=Column(Integer,autoincrement=True)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    
    # Relationship with Customer
    
    order_items = relationship('OrderItem', backref='order')


class OrderItem(Base):
    __tablename__="order_items"

    id=Column(Integer,primary_key=True,autoincrement=True)
    order_quantity= Column(Integer,nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    
    # Relationship with Product and orders table
    

