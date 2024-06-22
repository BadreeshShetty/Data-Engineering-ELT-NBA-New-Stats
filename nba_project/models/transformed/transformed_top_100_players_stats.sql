-- models/transformed/transformed_top_100_players_stats.sql
WITH raw_stats AS (
    SELECT
        PLAYER_ID,
        RANK,
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
    FROM {{ ref('staging_top_100_players_stats') }}
),
sorted_stats AS (
    SELECT *
    FROM raw_stats
    ORDER BY PTS DESC
)
SELECT
    PLAYER_ID,
    RANK,
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
    PPG,
    APG,
    RPG,
    BPG,
    SPG,
    FG_PERCENT,
    FG3_PERCENT,
    FT_PERCENT
FROM sorted_stats

