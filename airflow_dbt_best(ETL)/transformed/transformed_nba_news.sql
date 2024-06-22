-- models/transformed/transformed_nba_news.sql
WITH raw_news AS (
    SELECT
        title,
        description,
        url,
        news_source,
        published_at,
        author,
        content
    FROM {{ ref('staging_nba_news') }}
)
SELECT * FROM raw_news
