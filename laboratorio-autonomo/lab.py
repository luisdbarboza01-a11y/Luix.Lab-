"""Offline, reproducible CSV profiling for Luix° Lab Autónomo v1."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


class LabError(ValueError):
    """Raised when an input dataset cannot be safely profiled."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _number(value: str) -> float | None:
    value = value.strip()
    if value == "":
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def profile_csv(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise LabError(f"Input file does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            if not headers:
                raise LabError("CSV has no header row")
            if any(not h or not h.strip() for h in headers):
                raise LabError("CSV contains an empty column name")
            if len(set(headers)) != len(headers):
                raise LabError("CSV contains duplicate column names")
            rows = list(reader)
    except UnicodeDecodeError as exc:
        raise LabError("CSV must be UTF-8 encoded") from exc
    if not rows:
        raise LabError("CSV contains no data rows")
    if any(None in row for row in rows):
        raise LabError("CSV contains rows with more values than headers")

    columns: dict[str, Any] = {}
    for header in headers:
        values = [row.get(header, "") for row in rows]
        missing = sum(value is None or value.strip() == "" for value in values)
        numbers = [_number(value or "") for value in values]
        numeric = [n for n in numbers if n is not None]
        stats = None
        if numeric and len(numeric) + missing == len(values):
            ordered = sorted(numeric)
            count = len(ordered)
            median = (ordered[count // 2] if count % 2 else
                      (ordered[count // 2 - 1] + ordered[count // 2]) / 2)
            stats = {
                "count": count,
                "min": min(ordered),
                "max": max(ordered),
                "mean": sum(ordered) / count,
                "median": median,
            }
        columns[header] = {
            "missing_count": missing,
            "non_missing_count": len(values) - missing,
            "numeric_statistics": stats,
        }

    return {
        "profile_version": "1.0",
        "source_file": path.name,
        "source_sha256": sha256_file(path),
        "row_count": len(rows),
        "column_count": len(headers),
        "columns": columns,
        "method": "UTF-8 CSV parsing; blank cells treated as missing; finite numeric values summarized descriptively",
        "limitations": [
            "Descriptive profiling only; no causal inference.",
            "Blank cells remain missing and are never imputed as zero.",
            "A column is summarized numerically only when every non-missing value is finite numeric data.",
        ],
    }


def write_outputs(profile: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "profile.json"
    report_path = output_dir / "report.md"
    json_tmp = json_path.with_suffix(".json.tmp")
    report_tmp = report_path.with_suffix(".md.tmp")
    json_tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Informe de perfilado", "",
        f"- Archivo: `{profile['source_file']}`",
        f"- SHA-256: `{profile['source_sha256']}`",
        f"- Filas: {profile['row_count']}",
        f"- Columnas: {profile['column_count']}", "",
        "## Columnas", "",
        "| Columna | No ausentes | Ausentes | Estadísticas numéricas |",
        "|---|---:|---:|---|",
    ]
    for name, data in profile["columns"].items():
        stats = data["numeric_statistics"]
        rendered = "—" if stats is None else (
            f"n={stats['count']}, min={stats['min']}, max={stats['max']}, "
            f"media={stats['mean']:.6g}, mediana={stats['median']:.6g}"
        )
        lines.append(f"| {name} | {data['non_missing_count']} | {data['missing_count']} | {rendered} |")
    lines += ["", "## Método", "", profile["method"], "", "## Limitaciones", ""]
    lines += [f"- {item}" for item in profile["limitations"]]
    report_tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_tmp.replace(json_path)
    report_tmp.replace(report_path)
    return json_path, report_path
