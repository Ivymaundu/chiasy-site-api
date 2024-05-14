def fetch_sales(db: Session = Depends(get_db)):
    sales=db.query(Sale).all()
    return sales