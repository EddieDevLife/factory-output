from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DELIVERIES_DIR = ROOT / "entregas"
LANDINGPAGE_DIR = ROOT / "landingpage"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def iter_delivery_dirs(deliveries_dir: Path) -> Iterable[Path]:
    if not deliveries_dir.exists():
        return []
    return [p for p in deliveries_dir.iterdir() if p.is_dir()]


def find_first(path: Path, names: tuple[str, ...], max_depth: int = 6) -> Path | None:
    # BFS so shallow files win
    queue: list[tuple[Path, int]] = [(path, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            for child in current.iterdir():
                if child.is_file() and child.name in names:
                    return child
            for child in current.iterdir():
                if child.is_dir():
                    queue.append((child, depth + 1))
        except Exception:
            continue
    return None


def find_all(path: Path, filename: str, max_depth: int = 8) -> list[Path]:
    results: list[Path] = []
    queue: list[tuple[Path, int]] = [(path, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            for child in current.iterdir():
                if child.is_file() and child.name == filename:
                    results.append(child)
            for child in current.iterdir():
                if child.is_dir():
                    queue.append((child, depth + 1))
        except Exception:
            continue
    return results


@dataclass(frozen=True)
class DeliveryRecord:
    delivery_name: str
    delivery_path: str
    updated_at: str
    metadata_path: str | None
    product_name: str | None
    product_slug: str | None
    run_label: str | None
    packaged_at: str | None
    elapsed_seconds: float | None
    validation_status: str | None
    agents_count: int | None
    models: dict[str, int]


def _as_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def summarize_models(agents: Any) -> dict[str, int]:
    if not isinstance(agents, list):
        return {}
    out: dict[str, int] = {}
    for a in agents:
        if not isinstance(a, dict):
            continue
        model = a.get("llm_model") or a.get("model")
        if isinstance(model, str) and model.strip():
            out[model] = out.get(model, 0) + 1
    return out


def load_delivery_record(delivery_dir: Path) -> DeliveryRecord:
    stat = delivery_dir.stat()
    updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )

    # Prefer new Hive metadata.json if present anywhere inside
    metadata_candidates = find_all(delivery_dir, "metadata.json")
    metadata_path = metadata_candidates[0] if metadata_candidates else None
    metadata = safe_read_json(metadata_path) if metadata_path else None

    product_name = None
    product_slug = None
    run_label = None
    packaged_at = None
    elapsed_seconds = None
    validation_status = None
    agents_count = None
    models: dict[str, int] = {}

    if isinstance(metadata, dict):
        product_name = _as_str(metadata.get("product_name"))
        product_slug = _as_str(metadata.get("product_slug"))
        run_label = _as_str(metadata.get("run_label"))
        packaged_at = _as_str(metadata.get("packaged_at") or metadata.get("generated_at"))

        run_metrics = metadata.get("run_metrics") or metadata.get("runMetrics")
        if isinstance(run_metrics, dict):
            elapsed_seconds = _as_float(run_metrics.get("elapsed_seconds"))

        validation = metadata.get("validation")
        if isinstance(validation, dict):
            validation_status = _as_str(validation.get("status"))

        counts = metadata.get("counts")
        if isinstance(counts, dict):
            agents_count = _as_int(counts.get("agents"))

        agents = metadata.get("agents")
        if agents_count is None and isinstance(agents, list):
            agents_count = len(agents)
        models = summarize_models(agents)

    return DeliveryRecord(
        delivery_name=delivery_dir.name,
        delivery_path=str(delivery_dir.relative_to(ROOT)),
        updated_at=updated_at,
        metadata_path=str(metadata_path.relative_to(ROOT)) if metadata_path else None,
        product_name=product_name,
        product_slug=product_slug,
        run_label=run_label,
        packaged_at=packaged_at,
        elapsed_seconds=elapsed_seconds,
        validation_status=validation_status,
        agents_count=agents_count,
        models=models,
    )


def export_site(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [load_delivery_record(p) for p in iter_delivery_dirs(DELIVERIES_DIR)]
    records.sort(key=lambda r: r.updated_at, reverse=True)

    deliveries_json = {
        "generated_at": utc_now_iso(),
        "deliveries": [
            {
                **{
                    "delivery_name": r.delivery_name,
                    "delivery_path": r.delivery_path,
                    "updated_at": r.updated_at,
                    "metadata_path": r.metadata_path,
                    "product_name": r.product_name,
                    "product_slug": r.product_slug,
                    "run_label": r.run_label,
                    "packaged_at": r.packaged_at,
                    "elapsed_seconds": r.elapsed_seconds,
                    "validation_status": r.validation_status,
                    "agents_count": r.agents_count,
                },
                "models": r.models,
            }
            for r in records
        ],
    }
    (out_dir / "deliveries_index.json").write_text(
        json.dumps(deliveries_json, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # CSV for easy ingestion/BI
    csv_path = out_dir / "runs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "delivery_name",
                "delivery_path",
                "updated_at",
                "metadata_path",
                "product_name",
                "product_slug",
                "run_label",
                "packaged_at",
                "elapsed_seconds",
                "validation_status",
                "agents_count",
                "models_json",
            ],
        )
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "delivery_name": r.delivery_name,
                    "delivery_path": r.delivery_path,
                    "updated_at": r.updated_at,
                    "metadata_path": r.metadata_path or "",
                    "product_name": r.product_name or "",
                    "product_slug": r.product_slug or "",
                    "run_label": r.run_label or "",
                    "packaged_at": r.packaged_at or "",
                    "elapsed_seconds": r.elapsed_seconds if r.elapsed_seconds is not None else "",
                    "validation_status": r.validation_status or "",
                    "agents_count": r.agents_count if r.agents_count is not None else "",
                    "models_json": json.dumps(r.models, ensure_ascii=False),
                }
            )

    # Preserve a simple artifacts listing for direct downloads.
    (out_dir / "artifacts.html").write_text(
        "\n".join(
            [
                "<!doctype html>",
                "<meta charset='utf-8'/>",
                "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
                "<title>agentix-vault artifacts</title>",
                "<h1>Artifacts</h1>",
                "<ul>",
                "<li><a href='./deliveries_index.json'>deliveries_index.json</a></li>",
                "<li><a href='./runs.csv'>runs.csv</a></li>",
                "</ul>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Publish the landing page as the Pages root (index.html) alongside the artifacts.
    if LANDINGPAGE_DIR.exists():
        for name in ("index.html", "style.css", "main.js"):
            src = LANDINGPAGE_DIR / name
            if src.exists() and src.is_file():
                (out_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        # Fallback: keep an index if landingpage/ isn't present.
        (out_dir / "index.html").write_text(
            "\n".join(
                [
                    "<!doctype html>",
                    "<meta charset='utf-8'/>",
                    "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
                    "<title>agentix-vault artifacts</title>",
                    "<p>Landing page not found. See <a href='./artifacts.html'>artifacts</a>.</p>",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


def main() -> None:
    out_dir = Path(os.getenv("OUTPUT_DIR", "")).resolve() if os.getenv("OUTPUT_DIR") else ROOT / "site"
    export_site(out_dir)
    print(f"Wrote metrics site to: {out_dir}")


if __name__ == "__main__":
    main()
