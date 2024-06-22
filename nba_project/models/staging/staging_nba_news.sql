-- models/staging/staging_nba_news.sql
SELECT * FROM {{ source('nba_stats', 'nba_news') }}
