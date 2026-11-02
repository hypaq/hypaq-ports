# SPDX-License-Identifier: Apache-2.0
"""Run the published BAP CP-SAT adapter without changing or saving old results."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Import the existing module directly; no new package __init__.py is required.
from hypaq_ports.classical.cpsat import solve_berth_cpsat
from hypaq_ports.reference import load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path,
                        default=ROOT / "data/synthetic/berth_tiny_v1.json")
    parser.add_argument("--time-limit", type=float, default=10.0)
    args = parser.parse_args()
    result = solve_berth_cpsat(load_json(args.instance),
                              time_limit_seconds=args.time_limit,
                              num_workers=1, random_seed=42)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
