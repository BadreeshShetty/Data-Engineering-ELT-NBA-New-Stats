-- models/staging/staging_player_stats.sql
SELECT * FROM {{ source('nba_stats', 'player_stats') }}
