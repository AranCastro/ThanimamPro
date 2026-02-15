from typing import Optional

from ugp.config import UGPConfig
from ugp.core.registry import resolve_engine
from ugp.models import PTEnsemble, ThermoDataset, UncertaintyConfig
from ugp.uncertainty.bootstrap import bootstrap_ensemble


def run_pipeline(
    dataset: ThermoDataset,
    engine_name: Optional[str],
    config: UGPConfig,
    uncertainty: Optional[UncertaintyConfig] = None,
) -> PTEnsemble:
    engine_factory = resolve_engine(engine_name)
    engine = engine_factory(config)
    base_results = engine.run(dataset)

    if config.uncertainty_enabled and uncertainty:
        return bootstrap_ensemble(engine, dataset, uncertainty)

    return base_results

