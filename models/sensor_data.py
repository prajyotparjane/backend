from sqlalchemy import Column, Integer, Float, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)

    N = Column(Float)
    P = Column(Float)
    K = Column(Float)

    Temperature = Column(Float)
    Humidity = Column(Float)
    pH = Column(Float)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())