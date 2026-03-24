# backend/app/db/base.py
"""
Database base configuration module.
This file sets up the declarative base for SQLAlchemy ORM models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create a base class for all database models
# All model classes will inherit from this base
Base = declarative_base()

# This class provides the foundation for defining database tables
# as Python classes. SQLAlchemy uses this to map Python objects
# to database tables.