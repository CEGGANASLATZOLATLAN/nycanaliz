"""Grafik yardımcıları: ortak stil, kaynak notu, kaydetme.

Grafik standardı: başlık bir SORUYA cevap verir, eksenler Türkçe,
kaynak notu sağ altta.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PROJE_KOKU = Path(__file__).resolve().parent.parent
FIGURES = PROJE_KOKU / "ciktilar" / "grafikler"
MAPS = PROJE_KOKU / "ciktilar" / "haritalar"

RENKLER = {
    "hafta içi": "#1f6f8b",
    "hafta sonu": "#e4572e",
    "vurgu": "#c1121f",
    "notr": "#8d99ae",
}


def stil() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    plt.rcParams["figure.figsize"] = (11, 6)
    plt.rcParams["axes.titlesize"] = 15
    plt.rcParams["axes.titleweight"] = "bold"


def kaydet(fig, ad: str, yil: int | None = None) -> None:
    """Kaynak notunu basıp ciktilar/grafikler/[<yil>/]<ad>.png olarak kaydeder."""
    donem = f", {yil}" if yil else ""
    fig.text(0.99, -0.01, f"Kaynak: MTA — data.ny.gov{donem}",
             ha="right", va="top", fontsize=8, color="gray")
    klasor = FIGURES / str(yil) if yil else FIGURES
    klasor.mkdir(parents=True, exist_ok=True)
    yol = klasor / f"{ad}.png"
    fig.savefig(yol, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"kaydedildi: {yol.relative_to(PROJE_KOKU)}")
