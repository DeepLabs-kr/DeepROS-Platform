from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .config import DataSettings
import logging

logger = logging.getLogger(__name__)

# Get settings
settings = DataSettings()

# Create SQLite engine with optimized settings for rosbag-like functionality
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=StaticPool,  # Better for single-threaded applications
    connect_args={
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 30,  # Connection timeout
    },
    # SQLite-specific optimizations
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_db() -> Session:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Import all models to ensure they are registered
        from .models import ros_message, recording_session, topic_info, message_index
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def close_db():
    """Close database connections."""
    engine.dispose()
    logger.info("Database connections closed") 