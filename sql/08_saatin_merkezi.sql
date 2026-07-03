-- SORU: Manhattan'da her saatin "merkez üssü" neresi? O saatte hayatı
--       asıl orada dönen istasyon hangisi?
-- Yöntem: Mutlak yolcu sayısı her saat Times Square'i verir (turist seli).
--         Onun yerine ORANSAL uzmanlık: istasyonun o saatteki yolcusu,
--         kendi günlük toplamının yüzde kaçı? (SUM() OVER PARTITION BY
--         istasyon). Her saatin şampiyonu ROW_NUMBER ile seçilir.
-- Not: Yıllık 1M+ yolcu filtresi, küçük istasyonların oran gürültüsünü eler.

WITH saatlik AS (
    SELECT
        gun_tipi,
        station_complex AS istasyon,
        saat,
        SUM(ridership)  AS yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway' AND borough = 'Manhattan'
    GROUP BY 1, 2, 3
),
pay AS (
    SELECT
        gun_tipi, istasyon, saat,
        yolcu * 1.0 / SUM(yolcu) OVER (PARTITION BY gun_tipi, istasyon) AS gun_ici_pay,
        SUM(yolcu) OVER (PARTITION BY gun_tipi, istasyon)               AS istasyon_toplam
    FROM saatlik
),
sirali AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY gun_tipi, saat
                           ORDER BY gun_ici_pay DESC) AS sira
    FROM pay
    WHERE istasyon_toplam > 1_000_000
)
SELECT
    saat,
    gun_tipi,
    istasyon,
    ROUND(100 * gun_ici_pay, 1) AS gun_ici_pay_pct
FROM sirali
WHERE sira = 1
ORDER BY saat, gun_tipi;
