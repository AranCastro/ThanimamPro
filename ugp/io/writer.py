import json
from pathlib import Path
from typing import Dict

from ugp.models import PTEnsemble


def write_json(result: PTEnsemble, path: str) -> None:
    payload: Dict[str, object] = {
        "summary": result.summary,
        "diagnostics": result.diagnostics,
        "results": [
            {
                "pressure_gpa": p.pressure_gpa,
                "temperature_c": p.temperature_c,
                "method": p.method,
                "provenance": p.provenance,
            }
            for p in result.results
        ],
    }
    Path(path).write_text(json.dumps(payload, indent=2))

