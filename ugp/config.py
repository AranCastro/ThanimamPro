from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class UGPConfig:
    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./.ugp_cache")
    default_engine: str = "thermocalc"
    log_level: str = "INFO"
    uncertainty_enabled: bool = True
    uncertainty_iterations: int = 200
    uncertainty_confidence: float = 0.95
    random_seed: Optional[int] = None

