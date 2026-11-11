from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import TemplateError, load_config, render_all, write_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repo-templates-gen")
    parser.add_argument("--config", required=True, help="Path to JSON configuration file")
    parser.add_argument("--out", required=True, help="Output directory (repository root)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)

    try:
        text = Path(args.config).read_text(encoding="utf-8")
    except OSError as e:
        print(f"error: cannot read config: {e}", file=sys.stderr)
        return 2

    try:
        config = load_config(text)
        files = render_all(config)
        write_all(files, Path(args.out), overwrite=args.force)
    except TemplateError as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
