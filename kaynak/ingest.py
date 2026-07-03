"""Aylık ham CSV'yi temiz Parquet'e çevirir.

Kullanım (proje kökünden):
    python kaynak/ingest.py 202310

Temizlik:
- ridership/transfers DOUBLE gelir (MTA tahmini değerler) → yuvarlanıp INTEGER
- georeference kolonu atılır (latitude/longitude zaten var)
- Kolon adları kaynaktakiyle aynı bırakılır

Not: Disk tasarrufu için ham CSV'ler Parquet'e çevrildikten sonra silinir
(bkz. scriptler/veri_boru_hatti.py) — veri SODA API'den her an yeniden çekilebilir.
"""

import sys
from pathlib import Path

import duckdb

PROJE_KOKU = Path(__file__).resolve().parent.parent
RAW = PROJE_KOKU / "veri" / "ham"
PROCESSED = PROJE_KOKU / "veri" / "islenmis"


def donustur(ay: str) -> Path:
    csv_path = RAW / f"mta_hourly_{ay}.csv"
    parquet_path = PROCESSED / f"mta_{ay}.parquet"
    duckdb.sql(f"""
        COPY (
            SELECT
                transit_timestamp,
                transit_mode,
                station_complex_id,
                station_complex,
                borough,
                payment_method,
                fare_class_category,
                CAST(ROUND(ridership) AS INTEGER)  AS ridership,
                CAST(ROUND(transfers) AS INTEGER)  AS transfers,
                latitude,
                longitude
            FROM read_csv('{csv_path}', header=true)
        ) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    return parquet_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for ay in sys.argv[1:]:
        p = donustur(ay)
        print(f"{ay}: → {p.stat().st_size / 1e6:.0f} MB Parquet")
