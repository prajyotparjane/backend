from database import engine
from models.user import User
from database import Base

Base.metadata.create_all(bind=engine)
