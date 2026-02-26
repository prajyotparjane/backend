from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import pandas as pd
import joblib
from sqlalchemy.orm import Session
import bcrypt
import json

from utils.fertilizer_calc import fertilizer_recommendation
from database import SessionLocal, Base, engine   # ✅ UPDATED IMPORT
from models.user import User
from models.prediction_history import PredictionHistory


SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24


# ================= AUTH =================
def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(authorization: str | None = Header(default=None)):
    if authorization is None:
        return 0
    if not authorization.startswith("Bearer "):
        return 0
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        return 0


def hash_password(password: str) -> str:
    password = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    password = password.encode("utf-8")[:72]
    return bcrypt.checkpw(password, hashed.encode("utf-8"))


# ================= LOAD MODEL =================
model, features, season_encoder = joblib.load("model/crop_model.pkl")


# ================= LOAD EXCEL =================
crop_df = pd.read_excel("data/crop.xlsx")

crop_df.columns = crop_df.columns.str.strip().str.capitalize()

if "Crop" not in crop_df.columns:
    raise Exception("Excel must contain 'Crop' column")

if "Season" not in crop_df.columns:
    raise Exception("Excel must contain 'Season' column")

crop_df["Crop"] = crop_df["Crop"].astype(str).str.strip()
crop_df["Season"] = crop_df["Season"].astype(str).str.strip().str.capitalize()

ideal_df = crop_df[["Crop", "N", "P", "K"]]
season_df = crop_df[["Crop", "Season"]]


# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 VERY IMPORTANT — CREATE TABLES AUTOMATICALLY
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= SCHEMAS =================
class SoilInput(BaseModel):
    N: float
    P: float
    K: float
    Temperature: float
    Humidity: float
    pH: float
    Season: str


class RegisterInput(BaseModel):
    username: str
    email: str
    password: str


class LoginInput(BaseModel):
    email: str
    password: str


# ================= REGISTER =================
@app.post("/register")
def register_user(data: RegisterInput, db: Session = Depends(get_db)):

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email exists")

    user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(user)
    db.commit()

    return {"message": "User registered"}


# ================= LOGIN =================
@app.post("/login")
def login_user(data: LoginInput, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_token(user.id)

    return {"token": token, "user": {"id": user.id}}


# ================= PREDICT =================
@app.post("/predict")
def predict_crop(
    data: SoilInput,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    selected_season = data.Season.strip().capitalize()

    try:
        season_encoded = season_encoder.transform([selected_season])[0]
    except:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid season. Use {list(season_encoder.classes_)}"
        )

    input_df = pd.DataFrame([{
        "N": data.N,
        "P": data.P,
        "K": data.K,
        "Temperature": data.Temperature,
        "Humidity": data.Humidity,
        "pH": data.pH,
        "Season": season_encoded
    }])

    input_df = input_df.reindex(columns=features, fill_value=0)

    proba = model.predict_proba(input_df)[0]
    classes = model.classes_

    ranked = [classes[i] for i in proba.argsort()[::-1]]

    results = []

    for crop_name in ranked:

        season_row = season_df[season_df["Crop"] == crop_name]
        if season_row.empty:
            continue

        crop_season = season_row.iloc[0]["Season"]

        if crop_season != selected_season:
            continue

        row = ideal_df[ideal_df["Crop"] == crop_name]
        if row.empty:
            continue

        deficiency = {
            "N": max(0, row.iloc[0]["N"] - data.N),
            "P": max(0, row.iloc[0]["P"] - data.P),
            "K": max(0, row.iloc[0]["K"] - data.K),
        }

        fertilizer = fertilizer_recommendation(deficiency)

        results.append({
            "crop": crop_name,
            "deficiency": deficiency,
            "fertilizer_recommendation": fertilizer
        })

        break

    if not results:
        results.append({
            "crop": "No suitable crop for selected season",
            "deficiency": {},
            "fertilizer_recommendation": []
        })

    if user_id != 0:
        history = PredictionHistory(
            user_id=user_id,
            N=data.N, P=data.P, K=data.K,
            Temperature=data.Temperature,
            Humidity=data.Humidity,
            pH=data.pH,
            result=json.dumps(results)
        )
        db.add(history)
        db.commit()

    return {"recommendations": results}


# ================= HISTORY =================
@app.get("/history")
def get_history(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    if user_id == 0:
        return []

    records = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .order_by(PredictionHistory.id.desc())
        .all()
    )

    return [{
        "N": r.N, "P": r.P, "K": r.K,
        "Temperature": r.Temperature,
        "Humidity": r.Humidity,
        "pH": r.pH,
        "result": json.loads(r.result)
    } for r in records]