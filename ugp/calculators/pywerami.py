from ugp.calculators.base import CalculatorEngine
from ugp.core.registry import register_engine
from ugp.models import PTEnsemble, PTPoint, ThermoDataset


@register_engine("pywerami")
def build_pywerami(config):
    return PyWeramiEngine(config)


class PyWeramiEngine(CalculatorEngine):
    def run(self, dataset: ThermoDataset) -> PTEnsemble:
        dummy = PTPoint(
            pressure_gpa=1.0,
            temperature_c=720.0,
            method="PyWerami",
            provenance={"note": "placeholder"},
        )
        return PTEnsemble(results=[dummy], summary={"status": "not-implemented"})

