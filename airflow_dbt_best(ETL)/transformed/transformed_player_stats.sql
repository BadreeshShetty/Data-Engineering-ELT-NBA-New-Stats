-- models/transformed/transformed_player_stats.sql
WITH raw_stats AS (
    SELECT
        PLAYER_ID,
        PLAYER,
        TEAM,
        GP,
        MIN,
        FGM,
        FGA,
        FG3M,
        FG3A,
        FTM,
        FTA,
        OREB,
        DREB,
        REB,
        AST,
        STL,
        BLK,
        TOV,
        PF,
        PTS,
        PTS / GP AS PPG,
        AST / GP AS APG,
        REB / GP AS RPG,
        BLK / GP AS BPG,
        STL / GP AS SPG,
        FGM / FGA AS FG_PERCENT,
        FG3M / FG3A AS FG3_PERCENT,
        FTM / FTA AS FT_PERCENT
    FROM {{ ref('staging_player_stats') }}
)
SELECT * FROM raw_stats
