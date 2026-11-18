import random
from statistics import mean, pstdev
from typing import List

from ugp.models import PTEnsemble, PTPoint, ThermoDataset, UncertaintyConfig


def _resample_dataset(dataset: ThermoDataset, rng: random.Random) -> ThermoDataset:
    picked = [rng.choice(dataset.analyses) for _ in dataset.analyses]
    return ThermoDataset(analyses=picked, reference_frame=dataset.reference_frame)


def _percentile(sorted_values: List[float], q: float) -> float:
    """Linear-interpolated percentile (q in [0, 1]) of an ascending list."""
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def bootstrap_ensemble(engine, dataset: ThermoDataset, config: UncertaintyConfig) -> PTEnsemble:
    if config.bootstrap_iterations < 1:
        raise ValueError("bootstrap_iterations must be at least 1")
    if not 0.0 < config.confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")

    rng = random.Random(config.random_seed)  # local RNG: no global-state side effects
    runs: List[PTPoint] = []
    statuses = set()
    for _ in range(config.bootstrap_iterations):
        result = engine.run(_resample_dataset(dataset, rng))
        runs.extend(result.results)
        if "status" in result.summary:
            statuses.add(result.summary["status"])

    if not runs:
        raise ValueError("engine returned no P-T results to summarise")

    pressures = sorted(r.pressure_gpa for r in runs)
    temps = sorted(r.temperature_c for r in runs)
    lo_q, hi_q = (1.0 - config.confidence) / 2.0, 1.0 - (1.0 - config.confidence) / 2.0
    summary = {
        "p_mean_gpa": mean(pressures),
        "p_std_gpa": pstdev(pressures) if len(pressures) > 1 else 0.0,
        "p_ci_gpa": [_percentile(pressures, lo_q), _percentile(pressures, hi_q)],
        "t_mean_c": mean(temps),
        "t_std_c": pstdev(temps) if len(temps) > 1 else 0.0,
        "t_ci_c": [_percentile(temps, lo_q), _percentile(temps, hi_q)],
        "iterations": config.bootstrap_iterations,
        "confidence": config.confidence,
    }
    if statuses:  # propagate e.g. "not-implemented" so placeholder output is not mistaken for a result
        summary["status"] = statuses.pop() if len(statuses) == 1 else sorted(statuses)
    return PTEnsemble(results=runs, summary=summary, diagnostics={"bootstrap": True})
