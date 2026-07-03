"""Aylık ham CSV'yi analiz öncesi doğrular.

Kullanım (proje kökünden):
    python scriptler/validate_ay.py veri/ham/mta_hourly_202310.csv

Kontroller:
- Şema beklenen kolonlarla uyuşuyor mu
- Ayın tüm günleri var mı; her gün en az 23 saat (DST geçiş günleri 23 saat
  olabilir: Mart'ta saat ileri alınınca 02:00 yoktur) ve yeterli satır var mı
- ridership NULL oranı

Çıkış kodu: 0 = TAM, 1 = EKSİK/SORUNLU.
"""

import calendar
import sys

import duckdb

BEKLENEN_KOLONLAR = [
    "transit_timestamp", "transit_mode", "station_complex_id",
    "station_complex", "borough", "payment_method", "fare_class_category",
    "ridership", "transfers", "latitude", "longitude", "georeference",
]

# Normal bir gün ~70 bin satır; kırıntı/eksik günü ayırt etmek için eşik
MIN_SATIR_PER_GUN = 30_000


def validate(csv_path: str) -> bool:
    print(f"\n=== {csv_path} ===")
    sorun = False

    kolonlar = [r[0] for r in
                duckdb.sql(f"DESCRIBE SELECT * FROM '{csv_path}'").fetchall()]
    if kolonlar != BEKLENEN_KOLONLAR:
        sorun = True
        print(f"[SORUN] Şema farklı! gelen: {kolonlar}")
    else:
        print("[OK] Şema beklendiği gibi")

    gunler = duckdb.sql(f"""
        SELECT CAST(transit_timestamp AS DATE) AS gun,
               COUNT(DISTINCT EXTRACT(hour FROM transit_timestamp)) AS saat,
               COUNT(*) AS satir
        FROM '{csv_path}' GROUP BY 1 ORDER BY 1
    """).fetchall()
    ilk_gun = gunler[0][0]
    ay_gun = calendar.monthrange(ilk_gun.year, ilk_gun.month)[1]
    tam = [g for g, saat, satir in gunler
           if saat >= 23 and satir >= MIN_SATIR_PER_GUN]
    toplam_satir = sum(satir for _, _, satir in gunler)
    print(f"Satır: {toplam_satir:,} | Gün: {len(gunler)}/{ay_gun} | "
          f"Tam gün: {len(tam)}/{ay_gun}")
    if len(tam) < ay_gun:
        sorun = True
        eksikler = [(str(g), saat, satir) for g, saat, satir in gunler
                    if saat < 23 or satir < MIN_SATIR_PER_GUN]
        print(f"[SORUN] Eksik/kırıntı günler: {eksikler[:5]}"
              f"{' ...' if len(eksikler) > 5 else ''}")
        if len(gunler) < ay_gun:
            print(f"[SORUN] Ayın {ay_gun - len(gunler)} günü hiç yok")

    bos = duckdb.sql(f"""
        SELECT COUNT(*) FILTER (ridership IS NULL) FROM '{csv_path}'
    """).fetchone()[0]
    if bos:
        sorun = True
        print(f"[SORUN] {bos:,} satırda ridership NULL")

    print("SONUÇ:", "EKSİK/SORUNLU ⚠️" if sorun else "TAM ✅")
    return not sorun


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(0 if all(validate(p) for p in sys.argv[1:]) else 1)
