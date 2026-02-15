from ugp.calculators.base import CalculatorEngine
from ugp.core.registry import register_engine
from ugp.models import PTEnsemble, PTPoint, ThermoDataset


@register_engine("thermocalc")
def build_thermocalc(config):
    return ThermoCalcEngine(config)


class ThermoCalcEngine(CalculatorEngine):
    def run(self, dataset: ThermoDataset) -> PTEnsemble:
        # Placeholder until THERMOCALC coupling is implemented.
        dummy = PTPoint(
            pressure_gpa=0.8,
            temperature_c=650.0,
            method="THERMOCALC",
            provenance={"note": "placeholder"},
        )
        return PTEnsemble(results=[dummy], summary={"status": "not-implemented"})

