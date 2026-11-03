from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab import profile_csv, write_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Luix° Lab Autónomo CSV profiler.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("laboratorio-autonomo/output"))
    args = parser.parse_args()
    profile = profile_csv(args.csv_file)
    json_path, report_path = write_outputs(profile, args.output)
    print(json.dumps({
        "status": "success",
        "rows": profile["row_count"],
        "columns": profile["column_count"],
        "sha256": profile["source_sha256"],
        "profile": str(json_path),
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
