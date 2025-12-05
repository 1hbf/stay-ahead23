import joblib
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn
from sqlalchemy.orm import Session
import models
from database import engine, get_db

# إنشاء الجداول
models.Base.metadata.create_all(bind=engine)

# تحميل الموديل
try:
    pipe = joblib.load('churn_prediction_pipeline.joblib')
except:
    pipe = None

app = FastAPI()

# إعدادات الحماية CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نموذج البيانات (المدخلات)
class CustomerData(BaseModel):
    customer_id: str
    gender: str = "Male"
    is_senior_user: str = "0"
    has_partner: str = "No"
    has_dependents: str = "No"
    subscription_tenure_months: int
    ProductEnabled: str = "Yes"
    OnlineSecurity: str = "No"
    OnlineBackup: str = "No"
    DeviceProtection: str = "No"
    TechSupport: str = "No"
    FeatureA: str = "No"
    FeatureB: str = "No"
    billing_cycle_type: str
    PaperlessBilling: str = "Yes"
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float
    PlanType: str = "Fiber optic"

@app.post("/predict")
def predict_churn(customer: CustomerData, db: Session = Depends(get_db)):
    try:
        input_data = customer.model_dump()
        c_id = input_data.pop("customer_id")
        
        # تحويل البيانات لجدول
        df_new = pd.DataFrame([input_data])
        
        churn_probability = 0.0
        risk_category = "Low"

        if pipe:
            # 1. الحصول على الاحتمالية (رقم بين 0 و 1)
            # نأخذ العمود رقم 1 الذي يمثل احتمالية "نعم سيغادر"
            prob_array = pipe.predict_proba(df_new)
            churn_probability = float(prob_array[:, 1][0])
            
            # 2. تطبيق الشروط (المنطق الخاص بك)
            # يمكنك تعديل هذه الأرقام للتحكم في الحساسية
            if churn_probability >= 0.75:
                risk_category = "High"
            elif churn_probability >= 0.35: # خفضنا المتوسط قليلاً ليكون حساساً أكثر
                risk_category = "Medium"
            else:
                risk_category = "Low"

        # 3. الحفظ في قاعدة البيانات (مع التفاصيل)
        existing = db.query(models.ChurnPredictionResult).filter(models.ChurnPredictionResult.customer_id == c_id).first()
        
        if existing:
            existing.risk_category = risk_category
            existing.churn_probability = churn_probability
            existing.tenure = customer.subscription_tenure_months
            existing.contract = customer.billing_cycle_type
            existing.payment_method = customer.PaymentMethod
            existing.monthly_charges = customer.MonthlyCharges
            existing.total_charges = customer.TotalCharges
        else:
            db_result = models.ChurnPredictionResult(
                customer_id=c_id,
                churn_probability=churn_probability,
                risk_category=risk_category,
                tenure=customer.subscription_tenure_months,
                contract=customer.billing_cycle_type,
                payment_method=customer.PaymentMethod,
                monthly_charges=customer.MonthlyCharges,
                total_charges=customer.TotalCharges
            )
            db.add(db_result)
            
        db.commit()
        
        return {
            "customer_id": c_id,
            "ai_decision": risk_category, # الفرونت ينتظر هذه القيمة
            "probability": round(churn_probability, 2), # أرسلنا الاحتمالية أيضاً للعلم
            "message": "تم التحليل والحفظ"
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/high-risk-users")
def get_high_risk_users(db: Session = Depends(get_db)):
   return db.query(models.ChurnPredictionResult)\
             .order_by(models.ChurnPredictionResult.id.desc())\
             .limit(50).all()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)