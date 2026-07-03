"""Uçtan uca veri boru hattı: indir → doğrula → Parquet → ham CSV'yi sil.

Kullanım (proje kökünden):
    python scriptler/veri_boru_hatti.py 202201 202407   # aralık (dahil)
    python scriptler/veri_boru_hatti.py 202310          # tek ay

Disk tasarrufu: ham CSV yalnızca dönüşüm sırasında diskte tutulur;
doğrulama BAŞARISIZSA silinmez (incelemek için kalır). Veri SODA API'den
her an yeniden indirilebilir.
"""

import calendar
import subprocess
import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

RAW = PROJE_KOKU / "veri" / "ham"

# 2020-2024 seti; 2025+ için dataset id 5wq4-mkjj kullanılmalı
DATASET = "wujg-7c2s"
URL_SABLON = ("https://data.ny.gov/resource/{ds}.csv"
              "?$where=transit_timestamp between '{bas}T00:00:00'"
              " and '{son}T23:59:59'&$limit=10000000")


def ay_listesi(bas: str, son: str) -> list[str]:
    aylar, y, m = [], int(bas[:4]), int(bas[4:])
    while f"{y}{m:02d}" <= son:
        aylar.append(f"{y}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return aylar


def indir(ay: str) -> Path:
    yil, m = int(ay[:4]), int(ay[4:])
    son_gun = calendar.monthrange(yil, m)[1]
    url = URL_SABLON.format(ds=DATASET, bas=f"{yil}-{m:02d}-01",
                            son=f"{yil}-{m:02d}-{son_gun}").replace(" ", "%20")
    hedef = RAW / f"mta_hourly_{ay}.csv"
    # urllib yerine curl: python.org Python'ının macOS'ta sertifika zinciri
    # eksik olabiliyor (CERTIFICATE_VERIFY_FAILED); curl sistem sertifikalarını kullanır
    sonuc = subprocess.run(
        ["curl", "-sf", "--retry", "3", "-o", str(hedef), url])
    if sonuc.returncode != 0:
        raise RuntimeError(f"{ay}: indirme başarısız (curl exit {sonuc.returncode})")
    return hedef


def calistir(komut: list[str]) -> bool:
    return subprocess.run(komut, cwd=PROJE_KOKU).returncode == 0


def main() -> None:
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    aylar = ay_listesi(args[0], args[1] if len(args) > 1 else args[0])
    py = str(PROJE_KOKU / "venv" / "bin" / "python")
    sorunlular = []

    for ay in aylar:
        parquet = PROJE_KOKU / "veri" / "islenmis" / f"mta_{ay}.parquet"
        if parquet.exists():
            print(f"{ay}: Parquet zaten var, atlandı")
            continue
        csv = RAW / f"mta_hourly_{ay}.csv"
        if not csv.exists():
            print(f"{ay}: indiriliyor...", flush=True)
            indir(ay)
        print(f"{ay}: {csv.stat().st_size / 1e6:.0f} MB indi, doğrulanıyor")
        if not calistir([py, "scriptler/validate_ay.py", str(csv)]):
            print(f"{ay}: DOĞRULAMA BAŞARISIZ — CSV incelenmek üzere bırakıldı")
            sorunlular.append(ay)
            continue
        calistir([py, "kaynak/ingest.py", ay])
        csv.unlink()
        print(f"{ay}: tamam, ham CSV silindi")

    print("\n=== ÖZET ===")
    print(f"istenen {len(aylar)} ay; sorunlu: {sorunlular or 'yok'}")
    sys.exit(1 if sorunlular else 0)


if __name__ == "__main__":
    main()
