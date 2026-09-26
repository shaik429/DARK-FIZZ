import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add app directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.database import Base

# import ALL your models here so Alembic can detect them
from app.models import *  

# this is the Alembic Config object
config = context.config

# Set the sqlalchemy.url dynamically using urllib parse for password safety
from urllib.parse import quote_plus
encoded_password = quote_plus(settings.DB_PASSWORD)
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{encoded_password}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
config.set_main_option('sqlalchemy.url', DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# point Alembic to your models' metadata
target_metadata = Base.metadata

# ... rest of the file (run_migrations_offline, run_migrations_online) stays the same