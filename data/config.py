from pydantic_settings import BaseSettings
from typing import Optional
import os


class DataSettings(BaseSettings):
    """Settings for the ROS data storage system."""
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./ros_data.db"
    DATABASE_ECHO: bool = False
    
    # Storage settings
    DATA_DIR: str = "./data_storage"
    MAX_FILE_SIZE_MB: int = 1000  # Maximum size for individual data files
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_LEVEL: int = 6  # 0-9, higher = more compression
    
    # Message settings
    MAX_MESSAGE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    MESSAGE_TIMEOUT_SECONDS: int = 30
    BATCH_SIZE: int = 1000  # Number of messages to process in a batch
    
    # Recording settings
    DEFAULT_RECORDING_DURATION: int = 3600  # 1 hour in seconds
    AUTO_SPLIT_RECORDINGS: bool = True
    SPLIT_INTERVAL_SECONDS: int = 3600  # Split recordings every hour
    
    # Playback settings
    DEFAULT_PLAYBACK_RATE: float = 1.0  # Real-time playback
    LOOP_PLAYBACK: bool = False
    START_TIME_OFFSET: float = 0.0
    
    # Indexing settings
    AUTO_INDEX_ENABLED: bool = True
    INDEX_INTERVAL_SECONDS: int = 60  # Rebuild index every minute
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "DATA_"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        os.makedirs(self.DATA_DIR, exist_ok=True) 