"""Bir yılın tüm analiz grafiklerini üretir.

Kullanım (proje kökünden):
    python scriptler/make_figures.py 2023

Çıktılar: ciktilar/grafikler/<yil>/*.png
Kısmi yıllar (ör. 2024 Ocak-Temmuz) da çalışır.
"""

import argparse
import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU))

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from kaynak.db import PROCESSED, baglan, sql_dosyasi_calistir
from kaynak.viz import RENKLER, kaydet, stil

SQL = PROJE_KOKU / "sql"

# Yıl bazında özel günler (anomali/seyir etiketleri). Yeni yıl → buraya ekle.
OZEL_GUNLER = {
    2022: {
        "2022-01-01": "Yılbaşı",
        "2022-01-29": "Kar fırtınası (Nor'easter)",
        "2022-05-30": "Memorial Day",
        "2022-07-04": "Bağımsızlık Günü",
        "2022-09-05": "İşçi Bayramı",
        "2022-11-24": "Şükran Günü",
        "2022-12-23": "Elliott kış fırtınası",
        "2022-12-25": "Noel",
    },
    2023: {
        "2023-01-01": "Yılbaşı",
        "2023-05-29": "Memorial Day",
        "2023-07-04": "Bağımsızlık Günü",
        "2023-09-04": "İşçi Bayramı",
        "2023-09-29": "Sel baskını (Ophelia)",
        "2023-11-23": "Şükran Günü",
        "2023-12-25": "Noel",
    },
    2024: {
        "2024-01-01": "Yılbaşı",
        "2024-05-27": "Memorial Day",
        "2024-06-19": "Juneteenth",
        "2024-07-04": "Bağımsızlık Günü",
    },
}

SEYIR_ETIKETLERI = {
    2022: ["2022-01-29", "2022-07-04", "2022-11-24", "2022-12-23"],
    2023: ["2023-01-01", "2023-07-04", "2023-09-29", "2023-11-23", "2023-12-25"],
    2024: ["2024-01-01", "2024-05-27", "2024-07-04"],
}

GUN_ADLARI = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
TR_AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
            "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
FARE_RENKLERI = {
    "Tam": "#1f6f8b", "Öğrenci": "#e4572e", "65+/Engelli": "#9d4edd",
    "Fair Fare (düşük gelir)": "#2a9d8f", "Sınırsız abonman": "#8d99ae",
}


def tr_ay_ekseni(ax):
    import matplotlib.ticker as mticker
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: TR_AYLAR[mdates.num2date(x).month - 1]))


def tr_tarih(t: pd.Timestamp) -> str:
    return f"{t.day} {TR_AYLAR[t.month - 1]}"


def fig_01_saatlik_nabiz(con, yil):
    df = sql_dosyasi_calistir(con, SQL / "01_saatlik_profil.sql").df()
    fig, ax = plt.subplots()
    for tip, grup in df.groupby("gun_tipi"):
        ax.plot(grup["saat"], grup["ortalama_yolcu"] / 1000,
                label=tip, color=RENKLER[tip], linewidth=2.5)
    ax.set_title(f"New York kaçta uyanıyor — ya da hiç uyuyor mu? ({yil})")
    ax.set_xlabel("Saat")
    ax.set_ylabel("Ortalama yolcu (bin kişi/saat)")
    ax.set_xticks(range(0, 24, 2))
    ax.legend(title=None)
    kaydet(fig, "fig_01_saatlik_nabiz", yil)


def fig_02_isi_haritasi(con, yil):
    import seaborn as sns
    df = con.sql("""
        WITH gunluk AS (
            SELECT tarih, haftanin_gunu, saat, SUM(ridership) AS yolcu
            FROM yolculuk WHERE transit_mode = 'subway'
            GROUP BY 1, 2, 3
        )
        SELECT haftanin_gunu, saat, AVG(yolcu) AS ort
        FROM gunluk GROUP BY 1, 2
    """).df()
    pivot = df.pivot(index="haftanin_gunu", columns="saat", values="ort") / 1000
    pivot.index = [GUN_ADLARI[i - 1] for i in pivot.index]
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(pivot, cmap="rocket_r", ax=ax,
                cbar_kws={"label": "Ortalama yolcu (bin/saat)"})
    ax.set_title(f"Metronun nabzı: hangi gün, hangi saat? ({yil})")
    ax.set_xlabel("Saat")
    ax.set_ylabel("")
    kaydet(fig, "fig_02_isi_haritasi", yil)


def fig_03_yillik_seyir(con, yil):
    df = sql_dosyasi_calistir(con, SQL / "04_hareketli_ortalama.sql").df()
    df["tarih"] = pd.to_datetime(df["tarih"])
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(df["tarih"], df["yolcu"] / 1e6,
            color=RENKLER["notr"], linewidth=0.8, alpha=0.45, label="Günlük yolcu")
    ax.plot(df["tarih"], df["hareketli_ort_7g"] / 1e6,
            color=RENKLER["hafta içi"], linewidth=2.2, label="7 günlük hareketli ort.")
    ax.margins(x=0.02)
    son_gun = df["tarih"].max()
    for i, tarih in enumerate(SEYIR_ETIKETLERI.get(yil, [])):
        eslesen = df.loc[df["tarih"] == pd.Timestamp(tarih), "yolcu"]
        if eslesen.empty:
            continue
        t = pd.Timestamp(tarih)
        # yıl kenarındaki etiketler içeri hizalanır, ardışıklar dikeyde şaşırtılır
        ha = "right" if (son_gun - t).days < 12 else (
             "left" if (t - df["tarih"].min()).days < 12 else "center")
        ax.annotate(OZEL_GUNLER[yil][tarih], (t, float(eslesen.iloc[0]) / 1e6),
                    textcoords="offset points",
                    xytext=(0, -28 - 14 * (i % 2)), ha=ha,
                    fontsize=8, color=RENKLER["vurgu"],
                    arrowprops=dict(arrowstyle="-", color=RENKLER["vurgu"], lw=0.8))
    ax.set_title(f"{yil}'te New York metrosu ne zaman durdu, ne zaman coştu?")
    ax.set_xlabel("")
    ax.set_ylabel("Günlük toplam yolcu (milyon)")
    tr_ay_ekseni(ax)
    ax.legend(loc="lower right")
    kaydet(fig, "fig_03_yillik_seyir", yil)


def fig_04_anomali(con, yil):
    df = con.sql("""
        WITH gunluk AS (
            SELECT tarih, haftanin_gunu, SUM(ridership) AS yolcu
            FROM yolculuk WHERE transit_mode = 'subway'
            GROUP BY 1, 2
        )
        SELECT tarih, yolcu,
               (yolcu - AVG(yolcu) OVER (PARTITION BY haftanin_gunu))
                   / STDDEV(yolcu) OVER (PARTITION BY haftanin_gunu) AS z
        FROM gunluk ORDER BY tarih
    """).df()
    df["tarih"] = pd.to_datetime(df["tarih"])
    fig, ax = plt.subplots(figsize=(13, 6))
    normal = df[df["z"].abs() < 2]
    anomali = df[df["z"].abs() >= 2]
    ax.scatter(normal["tarih"], normal["z"], s=12,
               color=RENKLER["notr"], alpha=0.6, label="Normal gün")
    ax.scatter(anomali["tarih"], anomali["z"], s=28,
               color=RENKLER["vurgu"], label="Anomali (|z| ≥ 2)")
    ax.axhline(2, ls="--", lw=0.8, color="gray")
    ax.axhline(-2, ls="--", lw=0.8, color="gray")
    ax.margins(x=0.02)
    ozel = OZEL_GUNLER.get(yil, {})
    en_uc = set(anomali.reindex(anomali["z"].abs()
                                .sort_values(ascending=False).index).head(6).index)
    son_gun, ilk_gun = df["tarih"].max(), df["tarih"].min()
    ozel_gunler = [pd.Timestamp(g) for g in ozel]
    sayac = 0
    for idx, r in anomali.iterrows():
        gun = str(r["tarih"].date())
        if gun in ozel:
            etiket = ozel[gun]
        elif idx in en_uc:
            # sözlükteki bir olayın 3 gün yakınındaki kuyruk günlerini etiketleme
            if ozel_gunler and min(abs((r["tarih"] - t).days)
                                   for t in ozel_gunler) <= 3:
                continue
            etiket = tr_tarih(r["tarih"])
        else:
            continue
        # ardışık etiketleri dikeyde şaşırt, yıl kenarındakileri içeri hizala
        kaydir = 11 * (sayac % 3)
        sayac += 1
        yukari = r["z"] > 0
        kenarda = (son_gun - r["tarih"]).days < 12
        ax.annotate(etiket, (r["tarih"], r["z"]),
                    textcoords="offset points",
                    xytext=(-6 if kenarda else 6,
                            (8 + kaydir) if yukari else (-14 - kaydir)),
                    ha="right" if kenarda else "left",
                    fontsize=8)
    ax.set_title(f"Hangi günler 'normal' değildi? ({yil})")
    ax.set_xlabel("")
    ax.set_ylabel("Z-skoru (aynı haftanın gününe göre)")
    tr_ay_ekseni(ax)
    ax.legend(loc="upper left")
    kaydet(fig, "fig_04_anomali", yil)


def fig_05_gece(con, yil):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    df = sql_dosyasi_calistir(con, SQL / "05_gece_endeksi.sql").df()
    df = df.sort_values("gece_endeksi")
    ax1.barh(df["borough"], df["gece_endeksi"], color=RENKLER["hafta içi"])
    ax1.set_xlim(0, df["gece_endeksi"].max() * 1.18)  # ‰ etiketi bara sığsın
    for _, r in df.iterrows():
        ax1.text(r["gece_endeksi"] + 0.5, r["borough"],
                 f"‰{r['gece_endeksi']:.0f}", va="center", fontsize=9)
    ax1.set_title(f"Hangi borough gece yaşıyor? ({yil})")
    ax1.set_xlabel("Gece yolcu payı (binde, 23:00–05:00)")

    ist = con.sql("""
        SELECT station_complex AS istasyon,
               ROUND(1000.0 * SUM(ridership) FILTER (saat >= 23 OR saat < 5)
                            / SUM(ridership), 1) AS endeks,
               SUM(ridership) AS toplam
        FROM yolculuk WHERE transit_mode = 'subway'
        GROUP BY 1 HAVING SUM(ridership) > 500000
        ORDER BY endeks DESC LIMIT 10
    """).df().sort_values("endeks")
    ist["istasyon"] = ist["istasyon"].str.slice(0, 34)
    ax2.barh(ist["istasyon"], ist["endeks"], color=RENKLER["vurgu"])
    ax2.set_title("Gecenin istasyonları")
    ax2.set_xlabel("Gece yolcu payı (binde)")
    fig.tight_layout()  # uzun istasyon adları sol panele taşmasın
    kaydet(fig, "fig_05_gece", yil)


def fig_06_istasyon_kumeleri(con, yil):
    from sklearn.cluster import KMeans

    df = con.sql("""
        WITH saatlik AS (
            SELECT station_complex AS istasyon, saat, SUM(ridership) AS yolcu
            FROM yolculuk
            WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
            GROUP BY 1, 2
        )
        SELECT istasyon, saat,
               yolcu * 1.0 / SUM(yolcu) OVER (PARTITION BY istasyon) AS pay
        FROM saatlik
        QUALIFY SUM(yolcu) OVER (PARTITION BY istasyon) > 100000
    """).df()
    mat = df.pivot(index="istasyon", columns="saat", values="pay").fillna(0)
    km = KMeans(n_clusters=4, n_init=10, random_state=42).fit(mat)
    mat["kume"] = km.labels_
    profiller = {k: g.drop(columns="kume").mean() for k, g in mat.groupby("kume")}
    boyutlar = {k: len(g) for k, g in mat.groupby("kume")}
    oranlar = {k: p.loc[16:19].sum() / p.loc[6:9].sum() for k, p in profiller.items()}
    sirali = sorted(oranlar, key=oranlar.get)
    ADLAR = ["Sabah zirveli (yatak odası)", "Çift zirveli (dengeli)",
             "Akşam ağırlıklı (karma-merkez)", "Sert akşam zirveli (iş/merkez)"]
    fig, ax = plt.subplots()
    for ad, kume in zip(ADLAR, sirali):
        profil = profiller[kume]
        ax.plot(profil.index, profil * 100, linewidth=2.2,
                label=f"{ad} — {boyutlar[kume]} istasyon")
    ax.set_title(f"İstasyonların günlük ritmi kaç tipe ayrılıyor? ({yil})")
    ax.set_xlabel("Saat")
    ax.set_ylabel("Günlük yolcunun saatteki payı (%)")
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    kaydet(fig, "fig_06_istasyon_kumeleri", yil)


def fig_07_fare_class(con, yil):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    df = sql_dosyasi_calistir(con, SQL / "06_fare_class.sql").df()
    for grup, g in df.groupby("grup"):
        ax1.plot(g["saat"], g["gun_ici_pay_pct"], label=grup,
                 color=FARE_RENKLERI[grup], linewidth=2.2)
    ax1.set_title(f"Kim hangi saatte metroda? ({yil}, hafta içi)")
    ax1.set_xlabel("Saat")
    ax1.set_ylabel("Grubun günlük yolcusundaki payı (%)")
    ax1.set_xticks(range(0, 24, 2))
    ax1.legend(fontsize=9)

    ogr = con.sql("""
        WITH g AS (
            SELECT CASE WHEN ay = 3 THEN 'Okul dönemi (Mart)'
                        ELSE 'Yaz tatili (Temmuz)' END AS donem,
                   saat, SUM(ridership) AS yolcu
            FROM yolculuk
            WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
              AND fare_class_category LIKE '%Students%' AND ay IN (3, 7)
            GROUP BY 1, 2
        )
        SELECT donem, saat,
               100.0 * yolcu / SUM(yolcu) OVER (PARTITION BY donem) AS pay
        FROM g ORDER BY donem, saat
    """).df()
    for (donem, g), renk in zip(ogr.groupby("donem"),
                                [RENKLER["hafta içi"], RENKLER["hafta sonu"]]):
        ax2.plot(g["saat"], g["pay"], label=donem, color=renk, linewidth=2.2)
    ax2.set_title("Öğrenci kartı: okul vs yaz")
    ax2.set_xlabel("Saat")
    ax2.set_ylabel("Günlük yolcudaki pay (%)")
    ax2.set_xticks(range(0, 24, 2))
    ax2.legend(fontsize=9)
    fig.tight_layout()
    kaydet(fig, "fig_07_fare_class", yil)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yil", type=int)
    yil = p.parse_args().yil
    if not list(PROCESSED.glob(f"mta_{yil}*.parquet")):
        sys.exit(f"veri/islenmis/ altında {yil} Parquet'i yok.")
    stil()
    con = baglan(yil)
    fig_01_saatlik_nabiz(con, yil)
    fig_02_isi_haritasi(con, yil)
    fig_03_yillik_seyir(con, yil)
    fig_04_anomali(con, yil)
    fig_05_gece(con, yil)
    fig_06_istasyon_kumeleri(con, yil)
    fig_07_fare_class(con, yil)
