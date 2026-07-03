-- SORU: New York'un hangi köşesi gece yaşıyor?
-- Yöntem: Gece = 23:00–04:59. Borough bazında gece payı (binde).
--         İstasyon bazlısı harita script'inde (koordinatlar veride hazır).

SELECT
    borough,
    SUM(ridership)                                       AS toplam_yolcu,
    SUM(ridership) FILTER (saat >= 23 OR saat < 5)       AS gece_yolcu,
    ROUND(1000.0 * SUM(ridership) FILTER (saat >= 23 OR saat < 5)
                 / SUM(ridership), 1)                    AS gece_endeksi  -- binde
FROM yolculuk
WHERE transit_mode = 'subway'
GROUP BY 1
-- verideki tek tük hatalı etiketli satırlar (ör. 2 yolculuk gösteren
-- "Staten Island subway") oranı ‰1000'e fırlatıyor; hacim filtresi şart
HAVING SUM(ridership) > 1_000_000
ORDER BY gece_endeksi DESC;
