from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DB_URI


engine = create_engine(
    DB_URI,
    pool_pre_ping=True,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

# sync connection
db_session = sessionmaker(bind=engine)()
