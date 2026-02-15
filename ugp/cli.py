import argparse
import json
from pathlib import Path

from ugp.config import UGPConfig
from ugp.core.pipeline import run_pipeline
from ugp.core.registry import registry
from ugp.io.reader import read_dataset
from ugp.io.writer import write_json
from ugp.models import UncertaintyConfig
import ugp.engines  # noqa: F401 ensures engines are registered


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified Geothermobarometry Platform (UGP)")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Run geothermobarometry on a dataset")
    run_cmd.add_argument("input", help="Path to dataset (e.g. JSON)")
    run_cmd.add_argument("-e", "--engine", help="Engine to use", default=None)
    run_cmd.add_argument("-o", "--output", help="Write results to JSON file", default=None)
    run_cmd.add_argument("--bootstrap", action="store_true", help="Enable bootstrap uncertainty")
    run_cmd.add_argument("--iterations", type=int, default=200, help="Bootstrap iterations")
    run_cmd.add_argument("--confidence", type=float, default=0.95, help="Confidence level")

    sub.add_parser("engines", help="List available engines")
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "engines":
        for name in registry.available():
            print(name)
        return

    if args.command == "run":
        dataset = read_dataset(args.input)
        config = UGPConfig(
            uncertainty_enabled=args.bootstrap,
            uncertainty_iterations=args.iterations,
            uncertainty_confidence=args.confidence,
        )
        uncertainty = None
        if args.bootstrap:
            uncertainty = UncertaintyConfig(
                bootstrap_iterations=args.iterations,
                confidence=args.confidence,
            )
        result = run_pipeline(dataset, args.engine, config, uncertainty)

        if args.output:
            write_json(result, args.output)
            print(f"Wrote results to {Path(args.output).resolve()}")
        else:
            print(json.dumps(result.summary, indent=2))


if __name__ == "__main__":
    main()
