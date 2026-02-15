import json
from pathlib import Path
from typing import Callable, Dict

from ugp.models import MineralAnalysis, SampleMetadata, ThermoDataset


def _read_json(path: Path) -> ThermoDataset:
    payload = json.loads(path.read_text())
    analyses = []
    for entry in payload.get("analyses", []):
        meta = SampleMetadata(**entry["metadata"])
        analyses.append(
            MineralAnalysis(
                mineral=entry["mineral"],
                oxides_wt_pct=entry["oxides_wt_pct"],
                metadata=meta,
            )
        )
    return ThermoDataset(analyses=analyses, reference_frame=payload.get("reference", "wt%"))


_READERS: Dict[str, Callable[[Path], ThermoDataset]] = {
    ".json": _read_json,
}


def read_dataset(path: str) -> ThermoDataset:
    file_path = Path(path)
    reader = _READERS.get(file_path.suffix.lower())
    if not reader:
        raise ValueError(f"No reader for extension '{file_path.suffix}'")
    return reader(file_path)

