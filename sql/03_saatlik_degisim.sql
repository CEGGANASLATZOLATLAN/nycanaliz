-- SORU: New York kaçta "patlıyor"? Saatten saate en sert sıçrama ne zaman?
-- Yöntem: LAG() ile bir önceki saate göre mutlak ve yüzdesel değişim.

WITH saatlik AS (
    SELECT
        saat,
        SUM(ridership) * 1.0 / COUNT(DISTINCT tarih) AS ort_yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
    GROUP BY 1
)
SELECT
    saat,
    ROUND(ort_yolcu)                                        AS ort_yolcu,
    ROUND(ort_yolcu - LAG(ort_yolcu) OVER (ORDER BY saat))  AS onceki_saate_fark,
    ROUND(100.0 * (ort_yolcu - LAG(ort_yolcu) OVER (ORDER BY saat))
               / LAG(ort_yolcu) OVER (ORDER BY saat), 1)    AS degisim_pct
FROM saatlik
ORDER BY saat;
