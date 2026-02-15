import random
from statistics import mean, pstdev
from typing import List

from ugp.models import PTEnsemble, PTPoint, ThermoDataset, UncertaintyConfig


def _resample_dataset(dataset: ThermoDataset) -> ThermoDataset:
    picked = [random.choice(dataset.analyses) for _ in dataset.analyses]
    return ThermoDataset(analyses=picked, reference_frame=dataset.reference_frame)


def bootstrap_ensemble(engine, dataset: ThermoDataset, config: UncertaintyConfig) -> PTEnsemble:
    if config.random_seed is not None:
        random.seed(config.random_seed)

    runs: List[PTPoint] = []
    for _ in range(config.bootstrap_iterations):
        resampled = _resample_dataset(dataset)
        result = engine.run(resampled)
        runs.extend(result.results)

    pressures = [r.pressure_gpa for r in runs]
    temps = [r.temperature_c for r in runs]
    summary = {
        "p_mean_gpa": mean(pressures),
        "p_std_gpa": pstdev(pressures) if len(pressures) > 1 else 0.0,
        "t_mean_c": mean(temps),
        "t_std_c": pstdev(temps) if len(temps) > 1 else 0.0,
        "iterations": config.bootstrap_iterations,
        "confidence": config.confidence,
    }
    return PTEnsemble(results=runs, summary=summary, diagnostics={"bootstrap": True})

