from pydantic_settings import BaseSettings
from typing import Optional


class BrokerSettings(BaseSettings):
    """Settings for the MQTT Broker"""
    
    # MQTT Server Settings
    mqtt_host: str = "0.0.0.0"
    mqtt_port: int = 1883
    mqtt_keepalive: int = 60
    mqtt_max_connections: int = 1000
    
    # WebSocket Settings
    websocket_host: str = "0.0.0.0"
    websocket_port: int = 9001
    websocket_enabled: bool = True
    
    # Authentication Settings
    enable_auth: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    
    # TLS/SSL Settings
    enable_tls: bool = False
    tls_cert_file: Optional[str] = None
    tls_key_file: Optional[str] = None
    tls_ca_file: Optional[str] = None
    
    # Logging Settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance Settings
    max_message_size: int = 268435455  # 256MB
    max_inflight_messages: int = 20
    max_queued_messages: int = 100
    
    # ROS Integration Settings
    ros_domain_prefix: str = "ros/"
    enable_ros_integration: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "BROKER_"


# Global settings instance
settings = BrokerSettings() 