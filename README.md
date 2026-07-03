# NYC Analiz

![24 saatte New York'un nabzı](ciktilar/grafikler/nabiz_24saat_2023.gif)

MTA'in saatlik metro yolculuk verisiyle New York'un günlük ritmi.
2022 başından 2024 Temmuz'una kadar tüm istasyon kayıtları DuckDB ve
Python ile işlendi.


## Grafikler

![Saatlik nabız](ciktilar/grafikler/2023/fig_01_saatlik_nabiz.png)
*New York kaçta uyanıyor — ya da hiç uyuyor mu?*

![Anomaliler](ciktilar/grafikler/2023/fig_04_anomali.png)
*Hangi günler "normal" değildi?*

![Gece](ciktilar/grafikler/2023/fig_05_gece.png)
*Hangi borough, hangi istasyon gece yaşıyor?*

![Kart tipleri](ciktilar/grafikler/2023/fig_07_fare_class.png)
*Kim hangi saatte metroda?*

![İstasyon kümeleri](ciktilar/grafikler/2023/fig_06_istasyon_kumeleri.png)
*İstasyonların günlük ritmi kaç tipe ayrılıyor?*

İnteraktif gece haritası `ciktilar/haritalar/` altında (indirip tarayıcıda açın).
Tüm yılların grafikleri `ciktilar/grafikler/` altında.

## Veri

- Kaynak: [MTA Subway Hourly Ridership](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-2020-2024/wujg-7c2s) (data.ny.gov)

## Çalıştırma

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python scriptler/veri_boru_hatti.py 202201 202407   # indir + doğrula + Parquet
python scriptler/make_figures.py 2023               # yıl grafikleri
python scriptler/make_gece_haritasi.py 2023         # istasyon gece haritası
python scriptler/make_gif.py 2023                   # animasyonlu harita
```

## Yapı

```
├── sql/         # DuckDB sorguları
├── kaynak/         # ingest, db, viz
├── scriptler/     # veri boru hattı ve grafik/harita üreticileri
├── data/        # işlenmiş veri (repoda değil)
└── ciktilar/     # grafikler ve haritalar
```
