"""Animasyonlu harita: 24 saatte istasyon istasyon New York'un nabzı (GIF).

Kullanım (proje kökünden):
    python scriptler/make_gif.py 2023

Çıktı: ciktilar/grafikler/nabiz_24saat_<yil>.gif
Her istasyon kendi günlük zirvesine göre normalize edilir (0-1):
harita "hangi istasyon ne zaman canlı" sorusunu gösterir.
"""

import argparse
import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

import json

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
# kaynak: github.com/dwillis/nyc-maps (NYC Open Data türevi)


def main(yil: int) -> None:
    con = baglan(yil)
    df = con.sql("""
        WITH gunluk AS (
            SELECT station_complex AS istasyon, tarih, saat,
                   SUM(ridership) AS yolcu
            FROM yolculuk
            WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
            GROUP BY 1, 2, 3
        ),
        ort AS (
            SELECT istasyon, saat, AVG(yolcu) AS ort
            FROM gunluk GROUP BY 1, 2
            QUALIFY SUM(AVG(yolcu)) OVER (PARTITION BY istasyon) > 1000
        )
        SELECT o.istasyon, o.saat, o.ort,
               k.lat, k.lon, k.toplam
        FROM ort o
        JOIN (SELECT station_complex AS istasyon,
                     AVG(latitude) lat, AVG(longitude) lon,
                     SUM(ridership) toplam
              FROM yolculuk WHERE transit_mode = 'subway'
              GROUP BY 1) k USING (istasyon)
        ORDER BY 1, 2
    """).df()

    mat = df.pivot_table(index="istasyon", columns="saat", values="ort").fillna(0)
    norm = mat.div(mat.max(axis=1), axis=0).to_numpy()  # istasyon başına 0-1
    meta = (df[["istasyon", "lat", "lon", "toplam"]]
            .drop_duplicates("istasyon").set_index("istasyon").loc[mat.index])
    boyut = 4 + 40 * (meta["toplam"] / meta["toplam"].max()) ** 0.5

    fig, ax = plt.subplots(figsize=(8, 8.5), facecolor="#101018")
    ax.set_facecolor("#101018")
    ax.set_aspect(1 / np.cos(np.radians(40.7)))
    ax.axis("off")

    # arka plan: borough siluetleri (koyu dolgu, silik sınır)
    if BOROUGHS.exists():
        parcalar = []
        for f in json.loads(BOROUGHS.read_text())["features"]:
            geom = f["geometry"]
            halkalar = ([geom["coordinates"]] if geom["type"] == "Polygon"
                        else geom["coordinates"])
            parcalar += [Polygon(np.array(h[0])) for h in halkalar]
        ax.add_collection(PatchCollection(
            parcalar, facecolor="#1b1b2c", edgecolor="#34344c",
            linewidth=0.6, zorder=0))

    sc = ax.scatter(meta["lon"], meta["lat"], s=boyut, c=norm[:, 0],
                    cmap="magma", vmin=0, vmax=1, linewidths=0)
    baslik = ax.set_title("", fontsize=15, fontweight="bold", color="#eeeeee")
    fig.text(0.5, 0.05, "Her istasyon kendi günlük zirvesine göre (hafta içi)",
             ha="center", fontsize=8, color="#888888")
    fig.text(0.97, 0.02, f"Kaynak: MTA — data.ny.gov ({yil})",
             ha="right", fontsize=7, color="#888888")

    def kare(saat):
        sc.set_array(norm[:, saat])
        baslik.set_text(f"New York'un nabzı — saat {saat:02d}:00")
        return sc, baslik

    anim = FuncAnimation(fig, kare, frames=24)
    FIGURES.mkdir(parents=True, exist_ok=True)
    yol = FIGURES / f"nabiz_24saat_{yil}.gif"
    anim.save(yol, writer=PillowWriter(fps=2), dpi=110)
    plt.close(fig)
    print(f"kaydedildi: {yol.relative_to(PROJE_KOKU)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yil", type=int)
    main(p.parse_args().yil)
