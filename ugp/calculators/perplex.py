from ugp.calculators.base import CalculatorEngine
from ugp.core.registry import register_engine
from ugp.models import PTEnsemble, PTPoint, ThermoDataset


@register_engine("perplex")
def build_perplex(config):
    return PerplexEngine(config)


class PerplexEngine(CalculatorEngine):
    def run(self, dataset: ThermoDataset) -> PTEnsemble:
        dummy = PTPoint(
            pressure_gpa=0.9,
            temperature_c=700.0,
            method="Perple_X",
            provenance={"note": "placeholder"},
        )
        return PTEnsemble(results=[dummy], summary={"status": "not-implemented"})

