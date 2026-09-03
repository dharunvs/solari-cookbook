"""Generate or verify the committed FastAPI contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from noxyn_api.main import app

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "openapi.json"


def rendered_openapi() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rendered = rendered_openapi()
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            parser.error(
                f"{args.output} is stale; run `pnpm openapi:generate` and commit it"
            )
        return 0

    args.output.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
