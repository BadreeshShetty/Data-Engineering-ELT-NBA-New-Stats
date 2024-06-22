-- models/staging/staging_top_100_players_stats.sql
SELECT * FROM {{ source('nba_stats', 'top_100_players_stats') }}
