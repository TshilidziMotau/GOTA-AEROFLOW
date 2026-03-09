from app.db.session import engine
from app.models import models  # noqa: F401
from app.db.session import Base

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
