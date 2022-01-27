from typing import List, Optional
from pydantic import BaseSettings, Extra
from odrpc import DetectRequest

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
    auth_key: Optional[str] = ""
    class Config:
        env_prefix = 'server_'
        extra = Extra.ignore

class MqttBrokerConfig(BaseSettings):
    url: str
    port: Optional[int] = 1883
    user: Optional[str] = None
    password: Optional[str] = None
    class Config:
        env_prefix = 'mqttbroker_'
        extra = Extra.ignore

class MqttConfig(BaseSettings):
    broker: MqttBrokerConfig
    requests: List[DetectRequest]
    class Config:
        env_prefix = 'mqtt_'
        extra = Extra.ignore

class Config(BaseSettings):
    logger: Optional[LoggerConfig] = LoggerConfig()
    server: Optional[ServerConfig] = ServerConfig()
    doods: DoodsConfig
    mqtt: Optional[MqttConfig]
    class Config:
        extra = Extra.ignore
