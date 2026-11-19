"""Send a reproducible synthetic workload to the running YieldOps API."""

import argparse
import asyncio
import json

from yieldops.workload.generator import run_workload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--pattern", choices=("mixed", "classification", "bursty"), default="mixed"
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must both be positive")

    report = asyncio.run(
        run_workload(
            args.base_url,
            args.requests,
            args.concurrency,
            pattern=args.pattern,
            seed=args.seed,
        )
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
