from abc import ABC, abstractmethod
from typing import Any

from ugp.models import PTEnsemble, ThermoDataset


class CalculatorEngine(ABC):
    """Abstract interface for P-T calculators."""

    def __init__(self, config: Any) -> None:
        self.config = config

    @abstractmethod
    def run(self, dataset: ThermoDataset) -> PTEnsemble:
        raise NotImplementedError

