-- SORU: Kim hangi saatte yolda? Öğrenci, tam bilet, 65+/engelli ve
--       Fair Fare (düşük gelir) yolcuları metroyu aynı saatte mi kullanıyor?
-- Yöntem: Her grubun saatlik yolcusu kendi günlük toplamına oranlanır
--         (SUM() OVER (PARTITION BY grup)) — gruplar farklı büyüklükte.

WITH gruplu AS (
    SELECT
        CASE
            WHEN fare_class_category LIKE '%Full Fare%'          THEN 'Tam'
            WHEN fare_class_category LIKE '%Students%'           THEN 'Öğrenci'
            WHEN fare_class_category LIKE '%Seniors%'            THEN '65+/Engelli'
            WHEN fare_class_category LIKE '%Fair Fare%'          THEN 'Fair Fare (düşük gelir)'
            WHEN fare_class_category LIKE '%Unlimited%'          THEN 'Sınırsız abonman'
        END                     AS grup,
        saat,
        SUM(ridership)          AS yolcu
    FROM yolculuk
    WHERE transit_mode = 'subway' AND gun_tipi = 'hafta içi'
    GROUP BY 1, 2
)
SELECT
    grup,
    saat,
    yolcu,
    ROUND(100.0 * yolcu / SUM(yolcu) OVER (PARTITION BY grup), 2) AS gun_ici_pay_pct
FROM gruplu
WHERE grup IS NOT NULL
ORDER BY grup, saat;
