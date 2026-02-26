from sqlalchemy import Column, Integer, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base

class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    N = Column(Float)
    P = Column(Float)
    K = Column(Float)
    Temperature = Column(Float)
    Humidity = Column(Float)
    pH = Column(Float)

    result = Column(Text)

    # ✅ ADD THIS LINE (missing before)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
