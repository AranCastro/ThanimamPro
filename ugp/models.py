from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class SampleMetadata:
    sample_id: str
    rock_name: Optional[str] = None
    location: Optional[str] = None
    comments: Optional[str] = None


@dataclass
class MineralAnalysis:
    mineral: str
    oxides_wt_pct: Dict[str, float]
    metadata: SampleMetadata


@dataclass
class ThermoDataset:
    analyses: Sequence[MineralAnalysis]
    reference_frame: str = "wt%"


@dataclass
class PTPoint:
    pressure_gpa: float
    temperature_c: float
    method: str
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PTEnsemble:
    results: List[PTPoint]
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UncertaintyConfig:
    bootstrap_iterations: int = 200
    confidence: float = 0.95
    random_seed: Optional[int] = None

