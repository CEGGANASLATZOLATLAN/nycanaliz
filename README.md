# NYC Analiz — New York Saat Kaçta Nerede Yaşıyor?

![24 saatte New York'un nabzı](ciktilar/grafikler/nabiz_24saat_2023.gif)

MTA'in saatlik metro yolculuk verisiyle New York'un günlük ritmi.
2022 başından 2024 Temmuz'una tüm istasyon kayıtları DuckDB ve Python ile
işlendi. [İstanbul Analiz](https://github.com/CEGGANASLATZOLATLAN/istanbulanaliz)
projesinin kardeşi: aynı yöntem, başka bir şehir.

## Öne çıkan bulgular

- "Uyumayan şehir" efsanesi veride büyük ölçüde doğru: metro 7/24 çalışıyor ve gece trafiği hiçbir saatte sıfıra yaklaşmıyor. Hafta sonu gece yarısı, hafta içi öğlen kadar hareketli.
- Hafta içi klasik çift zirve var (sabah işe gidiş, akşam dönüş); akşam zirvesi sabahtan belirgin şekilde yüksek. Hafta sonu tek tepeli ve öğleden sonraya yayılmış.
- Gecenin istasyonları tam beklendiği yerde: Bushwick (Jefferson St) ve Greenwich Village (W 4 St, Christopher St) gece hayatının; Mets-Willets Point ise gece maçlarının izini taşıyor.
- Borough sıralamasında gecenin lideri Manhattan; Bronx ve Queens gece kullanımında Brooklyn'le başa baş.
- New York'u durduran günler resmi tatiller: yılın en boş metro günleri Şükran Günü, Noel ve Bağımsızlık Günü. Eylül 2023'teki sel baskını (Ophelia) da veride derin bir çukur olarak duruyor.
- Kart tipleri farklı şehirler anlatıyor: öğrenciler sabah erkenden okula akıyor, 65+ yolcular öğleden sonra ritmi yaşıyor, indirimli Fair Fare kullanıcıları sabah mesaisinin en sadık kitlesi.
- Öğrenci kartının profili yaz tatilinde tamamen değişiyor — sabah zirvesi kaybolup gün geç saate kayıyor.
- İstasyonlar ritimlerine göre ayrışıyor: sabah yoğun "yatak odası" duraklar, akşam yoğun iş bölgeleri ve gün boyu dengeli merkezler.

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

İnteraktif gece haritası `ciktilar/haritalar/` altında (indirip tarayıcıda açın);
tüm yılların grafikleri `ciktilar/grafikler/` altında.

## Veri

- Kaynak: [MTA Subway Hourly Ridership](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-2020-2024/wujg-7c2s) (data.ny.gov)
- Saatlik × istasyon kompleksi × ödeme tipi; istasyon koordinatları ve
  borough bilgisi veride hazır
- Veri repoda yok; boru hattı ay ay indirir, doğrular, Parquet'e çevirir
  ve ham CSV'yi siler (veri API'den her an yeniden çekilebilir)

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
