"""İstanbul vs New York: "uyumayan şehir" testi.

Kullanım (proje kökünden):
    python scriptler/istanbul_vs_nyc.py

Gereksinim: kardeş repo ../istanbul (istanbulanaliz) klonlanmış ve
2023 Parquet'leri üretilmiş olmalı (veri/islenmis/hourly_2023*.parquet).

Çıktı: ciktilar/grafikler/kiyas/istanbul_vs_nyc.png
Karşılaştırma 2023 hafta içi profilleri üzerinden; her şehir kendi günlük
toplamının yüzdesi olarak çizilir (mutlak hacimler kıyaslanamaz:
İstanbul verisi tüm toplu ulaşım, NYC verisi sadece metro).
"""

import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

import duckdb
import matplotlib.pyplot as plt

from kaynak.viz import FIGURES, stil

IST_PARQUET = PROJE_KOKU.parent / "istanbul" / "veri" / "islenmis"
YIL = 2023
RENK_IST = "#e4572e"
RENK_NYC = "#1f6f8b"


def sehir_profili(sorgu: str) -> "object":
    return duckdb.sql(sorgu).df().set_index("saat")["pay"]


def main() -> None:
    ist_glob = str(IST_PARQUET / f"hourly_{YIL}*.parquet")
    if not list(IST_PARQUET.glob(f"hourly_{YIL}*.parquet")):
        sys.exit(f"İstanbul Parquet'leri bulunamadı: {ist_glob}\n"
                 "istanbulanaliz reposunu klonlayıp ingest'i çalıştırın.")
    nyc_glob = str(PROJE_KOKU / "veri" / "islenmis" / f"mta_{YIL}*.parquet")

    ist = sehir_profili(f"""
        WITH g AS (
            SELECT transition_date AS tarih, transition_hour AS saat,
                   SUM(number_of_passenger) AS yolcu
            FROM '{ist_glob}'
            WHERE ISODOW(transition_date) <= 5
            GROUP BY 1, 2
        ),
        ort AS (SELECT saat, AVG(yolcu) AS ort FROM g GROUP BY 1)
        SELECT saat, 100.0 * ort / SUM(ort) OVER () AS pay FROM ort ORDER BY saat
    """)
    nyc = sehir_profili(f"""
        WITH g AS (
            SELECT CAST(transit_timestamp AS DATE) AS tarih,
                   EXTRACT(hour FROM transit_timestamp) AS saat,
                   SUM(ridership) AS yolcu
            FROM '{nyc_glob}'
            WHERE transit_mode = 'subway'
              AND ISODOW(CAST(transit_timestamp AS DATE)) <= 5
            GROUP BY 1, 2
        ),
        ort AS (SELECT saat, AVG(yolcu) AS ort FROM g GROUP BY 1)
        SELECT saat, 100.0 * ort / SUM(ort) OVER () AS pay FROM ort ORDER BY saat
    """)

    stil()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.plot(ist.index, ist.values, color=RENK_IST, linewidth=2.5,
             label="İstanbul (tüm toplu ulaşım)")
    ax1.plot(nyc.index, nyc.values, color=RENK_NYC, linewidth=2.5,
             label="New York (metro)")
    ax1.set_title(f"İki şehir, iki ritim ({YIL}, hafta içi)")
    ax1.set_xlabel("Yerel saat")
    ax1.set_ylabel("Günlük yolcunun saatteki payı (%)")
    ax1.set_xticks(range(0, 24, 2))
    ax1.legend()

    # Gece zoom'u: 20:00 → 05:00
    saatler = [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    x = range(len(saatler))
    ax2.bar([i - 0.2 for i in x], [ist[s] for s in saatler], width=0.4,
            color=RENK_IST, label="İstanbul")
    ax2.bar([i + 0.2 for i in x], [nyc[s] for s in saatler], width=0.4,
            color=RENK_NYC, label="New York")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels([f"{s:02d}" for s in saatler])
    ax2.set_title("Uyumayan şehir testi: gece saatleri")
    ax2.set_xlabel("Yerel saat (akşamdan sabaha)")
    ax2.set_ylabel("Günlük yolcudaki pay (%)")
    ax2.legend()

    klasor = FIGURES / "kiyas"
    klasor.mkdir(parents=True, exist_ok=True)
    fig.text(0.99, -0.01,
             "Kaynak: İBB Açık Veri + MTA data.ny.gov (2023, hafta içi)",
             ha="right", va="top", fontsize=8, color="gray")
    yol = klasor / "istanbul_vs_nyc.png"
    fig.savefig(yol, dpi=150, bbox_inches="tight")
    print(f"kaydedildi: {yol.relative_to(PROJE_KOKU)}")


if __name__ == "__main__":
    main()
