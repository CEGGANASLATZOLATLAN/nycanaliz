"""Isı haritası tarzı animasyon: 24 saatte New York'un gradyan nabzı (GIF).

Kullanım (proje kökünden):
    python scriptler/make_gif_isi.py 2023

Çıktı: ciktilar/grafikler/nabiz_isi_24saat_<yil>.gif

Nokta bulutu yerine sürekli yüzey: her istasyonun saatlik ortalama yolcusu
Gauss çekirdeğiyle yayılır (numpy ile ayrıştırılabilir konvolüsyon), kareler
arası gradyan geçiş görünümü oluşur. Renk ölçeği tüm güne sabittir: gece
kareleri gerçekten söner, sadece gece yaşayan bölgeler parlamaya devam eder.
"""

import argparse
import json
import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

from kaynak.db import baglan
from kaynak.viz import FIGURES

BOROUGHS = PROJE_KOKU / "veri" / "esleme" / "nyc_boroughs.geojson"

# Izgara ve çekirdek ayarları
LON_ARALIK = (-74.27, -73.68)
LAT_ARALIK = (40.49, 40.94)
GENISLIK = 520                    # ızgara hücre sayısı (boylam)
SIGMA_DERECE = 0.0045             # ~400 m Gauss yayılımı


def gauss_bulanikla(izgara: np.ndarray, sigma_hucre: float) -> np.ndarray:
    """Ayrıştırılabilir Gauss konvolüsyonu (scipy'siz)."""
    yaricap = int(4 * sigma_hucre)
    x = np.arange(-yaricap, yaricap + 1)
    cekirdek = np.exp(-(x ** 2) / (2 * sigma_hucre ** 2))
    cekirdek /= cekirdek.sum()
    ara = np.apply_along_axis(
        lambda s: np.convolve(s, cekirdek, mode="same"), 0, izgara)
    return np.apply_along_axis(
        lambda s: np.convolve(s, cekirdek, mode="same"), 1, ara)


def main(yil: int) -> None:
    con = baglan(yil)
    df = con.sql("""
        WITH gunluk AS (
            SELECT station_complex AS istasyon, tarih, saat,
                   SUM(ridership) AS yolcu
            FROM yolculuk
            WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
            GROUP BY 1, 2, 3
        )
        SELECT g.istasyon, g.saat, AVG(g.yolcu) AS ort, k.lat, k.lon
        FROM gunluk g
        JOIN (SELECT station_complex AS istasyon,
                     AVG(latitude) lat, AVG(longitude) lon
              FROM yolculuk WHERE transit_mode = 'subway'
              GROUP BY 1) k USING (istasyon)
        GROUP BY 1, 2, 4, 5
    """).df()

    yukseklik = int(GENISLIK * (LAT_ARALIK[1] - LAT_ARALIK[0])
                    / (LON_ARALIK[1] - LON_ARALIK[0]))
    hucre_boyu = (LON_ARALIK[1] - LON_ARALIK[0]) / GENISLIK
    sigma_hucre = SIGMA_DERECE / hucre_boyu

    kareler = []
    for saat in range(24):
        s = df[df["saat"] == saat]
        izgara, _, _ = np.histogram2d(
            s["lat"], s["lon"], bins=[yukseklik, GENISLIK],
            range=[LAT_ARALIK, LON_ARALIK], weights=s["ort"])
        kareler.append(gauss_bulanikla(izgara, sigma_hucre) ** 0.4)
    kareler = np.array(kareler)
    tavan = kareler.max()  # renk ölçeği tüm karelere sabit

    fig, ax = plt.subplots(figsize=(8, 8.2), facecolor="#0d0d16")
    ax.set_facecolor("#0d0d16")
    ax.set_xlim(LON_ARALIK)
    ax.set_ylim(LAT_ARALIK)
    ax.set_aspect(1 / np.cos(np.radians(40.7)))
    ax.axis("off")

    parcalar = []
    for f in json.loads(BOROUGHS.read_text())["features"]:
        geom = f["geometry"]
        halkalar = ([geom["coordinates"]] if geom["type"] == "Polygon"
                    else geom["coordinates"])
        parcalar += [Polygon(np.array(h[0])) for h in halkalar]
    ax.add_collection(PatchCollection(
        parcalar, facecolor="#181826", edgecolor="#3a3a55",
        linewidth=0.7, zorder=0))

    isi = ax.imshow(kareler[0], origin="lower", cmap="magma",
                    extent=[*LON_ARALIK, *LAT_ARALIK],
                    vmin=0, vmax=tavan,
                    alpha=np.clip(kareler[0] / tavan * 2.8, 0, 0.95),
                    zorder=1, interpolation="bilinear")
    baslik = ax.set_title("", fontsize=15, fontweight="bold", color="#eeeeee")
    fig.text(0.5, 0.04, "Saatlik ortalama yolcu yoğunluğu (hafta içi) — "
             "renk ölçeği tüm gün sabit", ha="center", fontsize=8, color="#888888")
    fig.text(0.97, 0.01, f"Kaynak: MTA — data.ny.gov ({yil})",
             ha="right", fontsize=7, color="#888888")

    def kare(saat):
        isi.set_data(kareler[saat])
        isi.set_alpha(np.clip(kareler[saat] / tavan * 2.8, 0, 0.95))
        baslik.set_text(f"New York'un nabzı — saat {saat:02d}:00")
        return isi, baslik

    anim = FuncAnimation(fig, kare, frames=24)
    FIGURES.mkdir(parents=True, exist_ok=True)
    yol = FIGURES / f"nabiz_isi_24saat_{yil}.gif"
    anim.save(yol, writer=PillowWriter(fps=2), dpi=110)
    plt.close(fig)
    print(f"kaydedildi: {yol.relative_to(PROJE_KOKU)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yil", type=int)
    main(p.parse_args().yil)
