-- models/staging/staging_nba_scores.sql
SELECT * FROM {{ source('nba_stats', 'nba_scores') }}
