-- SORU: Günlük toplam metro yolculuğu yıl boyunca nasıl seyretti?
-- Yöntem: AVG() OVER (... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
--         7 günlük hareketli ortalama + trendden sapma.

WITH gunluk AS (
    SELECT
        tarih,
        SUM(ridership) AS yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway'
    GROUP BY 1
)
SELECT
    tarih,
    yolcu,
    ROUND(AVG(yolcu) OVER (
        ORDER BY tarih ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ))                                                   AS hareketli_ort_7g,
    ROUND(100.0 * yolcu / AVG(yolcu) OVER (
        ORDER BY tarih ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) - 100, 1)                                          AS trendden_sapma_pct
FROM gunluk
ORDER BY tarih;
