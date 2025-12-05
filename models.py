from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ChurnPredictionResult(Base):
    __tablename__ = "churn_predictions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, index=True)
    
    
    tenure = Column(Integer)     
    contract = Column(String)       
    payment_method = Column(String)  
    monthly_charges = Column(Float) 
    total_charges = Column(Float)   
    

    churn_probability = Column(Float)
    risk_category = Column(String)
    prediction_date = Column(DateTime, default=datetime.now)

class RetentionAction(Base):
    __tablename__ = "retention_actions"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    action_type = Column(String)
    action_date = Column(DateTime, default=datetime.now)