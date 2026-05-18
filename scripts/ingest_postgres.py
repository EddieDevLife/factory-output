from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import psycopg

from export_metrics import DELIVERIES_DIR, DeliveryRecord, iter_delivery_dirs, load_delivery_record


ROOT = Path(__file__).resolve().parents[1]


SCHEMA_SQL = """
create table if not exists vault_deliveries (
  delivery_path text primary key,
  delivery_name text not null,
  updated_at timestamptz not null,
  metadata_path text null,
  product_name text null,
  product_slug text null,
  run_label text null,
  packaged_at timestamptz null,
  elapsed_seconds double precision null,
  validation_status text null,
  agents_count integer null,
  models jsonb not null default '{}'::jsonb
);
"""


UPSERT_SQL = """
insert into vault_deliveries (
  delivery_path, delivery_name, updated_at, metadata_path,
  product_name, product_slug, run_label, packaged_at,
  elapsed_seconds, validation_status, agents_count, models
)
values (
  %(delivery_path)s, %(delivery_name)s, %(updated_at)s, %(metadata_path)s,
  %(product_name)s, %(product_slug)s, %(run_label)s, %(packaged_at)s,
  %(elapsed_seconds)s, %(validation_status)s, %(agents_count)s, %(models)s::jsonb
)
on conflict (delivery_path) do update set
  delivery_name = excluded.delivery_name,
  updated_at = excluded.updated_at,
  metadata_path = excluded.metadata_path,
  product_name = excluded.product_name,
  product_slug = excluded.product_slug,
  run_label = excluded.run_label,
  packaged_at = excluded.packaged_at,
  elapsed_seconds = excluded.elapsed_seconds,
  validation_status = excluded.validation_status,
  agents_count = excluded.agents_count,
  models = excluded.models;
"""


def to_row(record: DeliveryRecord) -> dict:
    payload = asdict(record)
    payload["models"] = json.dumps(record.models, ensure_ascii=False)
    return payload


def main() -> None:
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    records = [load_delivery_record(p) for p in iter_delivery_dirs(DELIVERIES_DIR)]

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            for r in records:
                cur.execute(UPSERT_SQL, to_row(r))
        conn.commit()

    print(f"Upserted {len(records)} deliveries into Postgres")


if __name__ == "__main__":
    main()

