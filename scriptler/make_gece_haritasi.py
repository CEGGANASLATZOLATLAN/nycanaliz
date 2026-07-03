"""Gece haritası: istasyon bazlı gece endeksi (koordinatlar veride hazır).

Kullanım (proje kökünden):
    python scriptler/make_gece_haritasi.py 2023

Çıktı: ciktilar/haritalar/gece_haritasi_<yil>.html (folium, koyu tema)
Nokta rengi = gece payı (23:00–05:00, binde), boyut = toplam yolcu.
"""

import argparse
import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

import branca.colormap as cm
import folium

from kaynak.db import baglan
from kaynak.viz import MAPS


def main(yil: int) -> None:
    con = baglan(yil)
    df = con.sql("""
        SELECT station_complex AS istasyon, borough,
               AVG(latitude) AS lat, AVG(longitude) AS lon,
               SUM(ridership) AS toplam,
               ROUND(1000.0 * SUM(ridership) FILTER (saat >= 23 OR saat < 5)
                            / SUM(ridership), 1) AS endeks
        FROM yolculuk
        WHERE transit_mode = 'subway'
        GROUP BY 1, 2 HAVING SUM(ridership) > 100000
    """).df()

    m = folium.Map(location=[40.73, -73.95], zoom_start=11,
                   tiles="cartodbdark_matter")
    skala = cm.LinearColormap(
        ["#3a3a55", "#7161a8", "#c66bd1", "#ff9e6d", "#ffe066"],
        vmin=df["endeks"].quantile(0.02), vmax=df["endeks"].quantile(0.98),
        caption=f"Gece yolcu payı (binde, 23:00–05:00), {yil}")
    skala.add_to(m)

    maks = df["toplam"].max()
    for _, r in df.iterrows():
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=3 + 9 * (r["toplam"] / maks) ** 0.5,
            color=None, fill=True, fill_opacity=0.85,
            fill_color=skala(r["endeks"]),
            tooltip=(f"{r['istasyon']} ({r['borough']})<br>"
                     f"Gece payı: ‰{r['endeks']}"),
        ).add_to(m)

    baslik = (f'<h4 style="position:fixed;top:10px;left:50px;z-index:9999;'
              f'background:#111;color:#eee;padding:6px 12px;border-radius:4px">'
              f'Gece Haritası — New York geceleri nerede yaşıyor? ({yil})</h4>'
              f'<div style="position:fixed;bottom:10px;right:10px;z-index:9999;'
              f'background:#111;color:#aaa;padding:2px 8px;font-size:11px">'
              f'Kaynak: MTA — data.ny.gov</div>')
    m.get_root().html.add_child(folium.Element(baslik))

    MAPS.mkdir(parents=True, exist_ok=True)
    yol = MAPS / f"gece_haritasi_{yil}.html"
    m.save(str(yol))
    print(f"kaydedildi: {yol.relative_to(PROJE_KOKU)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yil", type=int)
    main(p.parse_args().yil)
