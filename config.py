from typing import List, Optional
from pydantic import BaseSettings, Extra

class DoodsDetectorConfig(BaseSettings):
    name: str
    type: str
    modelFile: str
    labelFile: Optional[str]
    hwAccel: Optional[bool] = False
    class Config:
        extra = Extra.ignore

class DoodsConfig(BaseSettings):
    detectors: List[DoodsDetectorConfig]
    auth_key: Optional[str] = ""
    class Config:
        env_prefix = 'doods_'
        extra = Extra.ignore

class LoggerConfig(BaseSettings):
    level: Optional[str] = "info" 
    class Config:
        env_prefix = 'logger_'
        extra = Extra.ignore

class ServerConfig(BaseSettings):
    host: Optional[str] = "0.0.0.0"
    port: Optional[int] = 8080
    class Config:
        env_prefix = 'server_'
        extra = Extra.ignore

class Config(BaseSettings):
    logger: Optional[LoggerConfig] = LoggerConfig()
    server: Optional[ServerConfig] = ServerConfig()
    doods: DoodsConfig
    class Config:
        extra = Extra.ignore
