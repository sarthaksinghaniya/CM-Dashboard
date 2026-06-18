from sqlalchemy.orm import declarative_base

Base = declarative_base()

# To be used by alembic to discover all models. Import your models here later:
from app.models.user import User
