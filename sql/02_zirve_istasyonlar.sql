-- SORU: Her istasyonun zirve saati kaç? "Sabah istasyonları" ve
--       "akşam istasyonları" nereler?
-- Yöntem: ROW_NUMBER() OVER (PARTITION BY istasyon ORDER BY yolcu DESC)

WITH istasyon_saat AS (
    SELECT
        station_complex AS istasyon,
        borough,
        saat,
        SUM(ridership) AS yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
    GROUP BY 1, 2, 3
),
sirali AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY istasyon ORDER BY yolcu DESC) AS sira,
        SUM(yolcu) OVER (PARTITION BY istasyon) AS istasyon_toplam
    FROM istasyon_saat
)
SELECT
    istasyon,
    borough,
    saat                                       AS zirve_saat,
    yolcu                                      AS zirve_saat_yolcu,
    istasyon_toplam,
    ROUND(100.0 * yolcu / istasyon_toplam, 1)  AS zirve_pay_pct
FROM sirali
WHERE sira = 1
ORDER BY istasyon_toplam DESC;
