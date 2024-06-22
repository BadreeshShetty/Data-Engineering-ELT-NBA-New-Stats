-- models/transformed/transformed_player_stats.sql
WITH aggregated_stats AS (
    SELECT
        PLAYER_ID,
        MIN(PLAYER) AS PLAYER,
        LISTAGG(DISTINCT TEAM, ' + ') AS TEAM,
        SUM(PTS) AS PTS,
        SUM(GP) AS GP,
        SUM(MIN) AS MIN,
        SUM(FGM) AS FGM,
        SUM(FGA) AS FGA,
        SUM(FG3M) AS FG3M,
        SUM(FG3A) AS FG3A,
        SUM(FTM) AS FTM,
        SUM(FTA) AS FTA,
        SUM(OREB) AS OREB,
        SUM(DREB) AS DREB,
        SUM(REB) AS REB,
        SUM(AST) AS AST,
        SUM(STL) AS STL,
        SUM(BLK) AS BLK,
        SUM(TOV) AS TOV,
        SUM(PF) AS PF
    FROM {{ ref('staging_player_stats') }}
    GROUP BY PLAYER_ID
),
player_stats AS (
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
    FROM aggregated_stats
),
top_500_players AS (
    SELECT *
    FROM player_stats
    ORDER BY PTS DESC
    LIMIT 500
)
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
    PPG,
    APG,
    RPG,
    BPG,
    SPG,
    FG_PERCENT,
    FG3_PERCENT,
    FT_PERCENT
FROM top_500_players