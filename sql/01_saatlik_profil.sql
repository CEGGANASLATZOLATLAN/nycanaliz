-- SORU: New York metrosunun ortalama saatlik yolcu profili nedir?
--       Hafta içi ile hafta sonu ritmi nasıl ayrışıyor?
-- Yöntem: Önce gün-saat bazında topla, sonra gün tipine göre ortala.
-- Kaynak view: yolculuk (kaynak/db.py); sadece metro (subway).

WITH gunluk_saatlik AS (
    SELECT
        tarih,
        gun_tipi,
        saat,
        SUM(ridership) AS yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway'
    GROUP BY 1, 2, 3
)
SELECT
    gun_tipi,
    saat,
    ROUND(AVG(yolcu)) AS ortalama_yolcu
FROM gunluk_saatlik
GROUP BY 1, 2
ORDER BY 1, 2;
