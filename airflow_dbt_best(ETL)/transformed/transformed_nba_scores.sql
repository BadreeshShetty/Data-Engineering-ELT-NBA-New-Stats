-- models/transformed/transformed_nba_scores.sql
WITH raw_scores AS (
    SELECT
        game_id,
        home_team,
        away_team,
        home_score,
        away_score,
        home_best_player_name,
        home_best_player_points,
        home_best_player_rebounds,
        home_best_player_assists,
        away_best_player_name,
        away_best_player_points,
        away_best_player_rebounds,
        away_best_player_assists
    FROM {{ ref('staging_nba_scores') }}
)
SELECT * FROM raw_scores
