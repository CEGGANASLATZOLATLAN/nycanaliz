"""DuckDB bağlantı yardımcıları.

Kullanım:
    from kaynak.db import baglan
    con = baglan(2023)   # tek yıl
    con = baglan()       # tüm yıllar
    con.sql("SELECT COUNT(*) FROM yolculuk").show()
"""

from pathlib import Path

import duckdb

PROJE_KOKU = Path(__file__).resolve().parent.parent
PROCESSED = PROJE_KOKU / "veri" / "islenmis"


def yolculuk_view(yil: int | None = None) -> str:
    desen = f"mta_{yil}*.parquet" if yil else "mta_*.parquet"
    return f"""
    CREATE OR REPLACE VIEW yolculuk AS
    SELECT
        *,
        CAST(transit_timestamp AS DATE)                     AS tarih,
        CAST(EXTRACT(hour FROM transit_timestamp) AS TINYINT) AS saat,
        YEAR(transit_timestamp)                             AS yil,
        MONTH(transit_timestamp)                            AS ay,
        ISODOW(CAST(transit_timestamp AS DATE))             AS haftanin_gunu,  -- 1=Pzt..7=Paz
        CASE WHEN ISODOW(CAST(transit_timestamp AS DATE)) <= 5
             THEN 'hafta içi' ELSE 'hafta sonu' END         AS gun_tipi
    FROM '{PROCESSED / desen}'
    """


def baglan(yil: int | None = None,
           db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """`yolculuk` view'ı hazır bir DuckDB bağlantısı döndürür."""
    con = duckdb.connect(db_path) if db_path else duckdb.connect()
    con.sql(yolculuk_view(yil))
    return con


def sql_dosyasi_calistir(con: duckdb.DuckDBPyConnection, sql_path: str | Path):
    """sql/ altındaki bir sorgu dosyasını çalıştırıp sonucu döndürür."""
    sorgu = Path(sql_path).read_text(encoding="utf-8")
    return con.sql(sorgu)
