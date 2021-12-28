from dataclasses import field
from pydantic.dataclasses import dataclass
from typing import Optional
from typing import Dict
from typing import List

@dataclass
class DetectRegion:
    top: float
    left: float
    bottom: float
    right: float
    detect: Dict[str, float]
    covers: bool = False

@dataclass
class DetectRequest:
    id: Optional[str] = None
    detector_name: Optional[str] = None
    data: str = ""
    preprocess: List[str] = field(default_factory=list)
    detect: Dict[str, float] = field(default_factory=dict)
    regions: List[DetectRegion] = field(default_factory=list)

@dataclass
class Detector:
    name: str
    type: str
    model: str
    labels: List[str] = field(default_factory=list)
    width: int = 0
    height: int = 0

@dataclass
class Detection:
    top: float = 0.0
    left: float = 0.0
    bottom: float = 0.0
    right: float = 0.0
    label: str = ""
    confidence: float = 0.0

@dataclass
class DetectResponse:
    id: Optional[str] = None
    detections: List[Detection] = field(default_factory=list)
    error: Optional[str] = None
