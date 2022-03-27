from typing import List, Optional
from pydantic import BaseSettings, Extra
from odrpc import MqttDetectRequest

class DoodsDetectorConfig(BaseSettings):
    name: str
    type: str
    modelFile: str
    labelFile: Optional[str]
    hwAccel: Optional[bool] = False
    numThreads: Optional[int] = 2
    class Config:
        extra = Extra.ignore

class DoodsBoxesConfig(BaseSettings):
    enabled: Optional[bool] = True
    boxColor: Optional[List[int]] = [0, 255, 0]
    boxThickness: Optional[int] = 1
    fontScale: Optional[float] = 1.2
    fontColor: Optional[List[int]] = [0, 255, 0]
    fontThickness: Optional[int] = 2

class DoodsRegionsConfig(BaseSettings):
    enabled: Optional[bool] = True
    boxColor: Optional[List[int]] = [0, 255, 0]
    boxThickness: Optional[int] = 1
    fontScale: Optional[float] = 1.2
    fontColor: Optional[List[int]] = [0, 255, 0]
    fontThickness: Optional[int] = 2

class DoodsGlobalsConfig(BaseSettings):
    enabled: Optional[bool] = True
    fontScale: Optional[float] = 1.2
    fontColor: Optional[List[int]] = [0, 255, 0]
    fontThickness: Optional[int] = 2

class DoodsConfig(BaseSettings):
    boxes: Optional[DoodsBoxesConfig] = DoodsBoxesConfig()
    regions: Optional[DoodsRegionsConfig] = DoodsRegionsConfig()
    globals: Optional[DoodsGlobalsConfig] = DoodsGlobalsConfig()
    detectors: List[DoodsDetectorConfig]
    log: Optional[str] = 'detections'
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
    auth_key: Optional[str] = ''
    metrics: Optional[bool] = True
    trace: Optional[bool] = False
    class Config:
        env_prefix = 'server_'
        extra = Extra.ignore

class MqttBrokerConfig(BaseSettings):
    host: Optional[str] = 'localhost'
    port: Optional[int] = 1883
    user: Optional[str] = None
    password: Optional[str] = None
    class Config:
        env_prefix = 'mqttbroker_'
        extra = Extra.ignore

class MqttConfig(BaseSettings):
    broker: MqttBrokerConfig
    requests: List[MqttDetectRequest]
    metrics: Optional[bool] = True
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
