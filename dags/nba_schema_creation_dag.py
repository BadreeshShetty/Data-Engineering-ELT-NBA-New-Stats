import airflow
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Constants
SNOWFLAKE_WAREHOUSE = 'NBA_STATS_WAREHOUSE'
SNOWFLAKE_DB = 'NBA_STATS_ANALYTICS'
SNOWFLAKE_SCHEMA = 'NBA_STATS'
SNOWFLAKE_STAGE = 'SNOW_S3_STAGE'
SNOWFLAKE_TABLE_SCORES = 'nba_scores'
SNOWFLAKE_TABLE_STATS = 'player_stats'
SNOWFLAKE_TABLE_NEWS = 'nba_news'
SNOWFLAKE_TABLE_100_STATS = 'top_100_players_stats'


# Define default arguments
default_args = {
    'owner': 'Airflow',
    'start_date': days_ago(2),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Initialize the DAG
dag = DAG(
    dag_id='nba_schema_creation_dag',
    default_args=default_args,
    description='Create Snowflake schema, tables, storage integration, stage, and file formats',
    schedule_interval='@once',
    catchup=False,
)

with dag:
    snowflake_create_db_schema = SQLExecuteQueryOperator(
        task_id='snowflake_create_db_schema',
        sql=f"""
        CREATE WAREHOUSE IF NOT EXISTS {SNOWFLAKE_WAREHOUSE} WITH WAREHOUSE_SIZE='x-small';
        CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DB};
        CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_SCHEMA};
        """,
        conn_id='snowflake_conn',
    )

    snowflake_create_storage_integration = SQLExecuteQueryOperator(
        task_id='snowflake_create_storage_integration',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE OR REPLACE STORAGE INTEGRATION SNOW_S3
        TYPE = EXTERNAL_STAGE
        STORAGE_PROVIDER = S3
        ENABLED = TRUE
        STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::767397772312:role/nba_news_stats_s3_snowflake'
        STORAGE_ALLOWED_LOCATIONS = ('s3://nba-stats-players/');
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_stage = SQLExecuteQueryOperator(
        task_id='snowflake_create_stage',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE OR REPLACE STAGE SNOW_S3_STAGE
        STORAGE_INTEGRATION = SNOW_S3
        URL = 's3://nba-stats-players/';
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_file_formats = SQLExecuteQueryOperator(
        task_id='snowflake_create_file_formats',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE OR REPLACE FILE FORMAT JSON_FORMAT
            TYPE = 'JSON'
            STRIP_OUTER_ARRAY = TRUE;
        CREATE OR REPLACE FILE FORMAT CSV_FORMAT 
            TYPE = CSV
            FIELD_DELIMITER = ','
            SKIP_HEADER = 1
            NULL_IF = ('NULL', 'null')
            EMPTY_FIELD_AS_NULL = TRUE;
        CREATE OR REPLACE FILE FORMAT PARQUET_FORMAT 
            TYPE = 'PARQUET';
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_table_scores = SQLExecuteQueryOperator(
        task_id='snowflake_create_table_scores',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE TABLE IF NOT EXISTS {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE_SCORES} (
            game_id STRING,
            home_team STRING,
            away_team STRING,
            home_score INT,
            away_score INT,
            home_best_player_name STRING,
            home_best_player_points NUMBER,
            home_best_player_rebounds NUMBER,
            home_best_player_assists NUMBER,
            away_best_player_name STRING,
            away_best_player_points NUMBER,
            away_best_player_rebounds NUMBER,
            away_best_player_assists NUMBER
        );
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_table_stats = SQLExecuteQueryOperator(
        task_id='snowflake_create_table_stats',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE TABLE IF NOT EXISTS {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE_STATS} (
            PLAYER_ID STRING,
            PLAYER STRING,
            TEAM STRING,
            GP NUMBER,
            MIN NUMBER,
            FGM NUMBER,
            FGA NUMBER,
            FG3M NUMBER,
            FG3A NUMBER,
            FTM NUMBER,
            FTA NUMBER,
            OREB NUMBER,
            DREB NUMBER,
            REB NUMBER,
            AST NUMBER,
            STL NUMBER,
            BLK NUMBER,
            TOV NUMBER,
            PF NUMBER,
            PTS NUMBER
        );
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_table_news = SQLExecuteQueryOperator(
        task_id='snowflake_create_table_news',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE TABLE IF NOT EXISTS {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE_NEWS} (
            title STRING,
            description STRING,
            url STRING,
            news_source STRING,
            published_at TIMESTAMP,
            author STRING,
            content STRING
        );
        """,
        conn_id='snowflake_conn'
    )

    snowflake_create_table_top_100_players_stats = SQLExecuteQueryOperator(
        task_id='snowflake_create_table_top_100_players_stats',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        CREATE TABLE IF NOT EXISTS {SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE_100_STATS} (
            PLAYER_ID STRING,
            RANK NUMBER,
            PLAYER STRING,
            TEAM STRING,
            GP NUMBER,
            MIN NUMBER,
            FGM NUMBER,
            FGA NUMBER,
            FG3M NUMBER,
            FG3A NUMBER,
            FTM NUMBER,
            FTA NUMBER,
            OREB NUMBER,
            DREB NUMBER,
            REB NUMBER,
            AST NUMBER,
            STL NUMBER,
            BLK NUMBER,
            TOV NUMBER,
            PF NUMBER,
            PTS NUMBER
        );
        """,
        conn_id='snowflake_conn'
    )

snowflake_create_db_schema >> snowflake_create_storage_integration >> snowflake_create_stage >> snowflake_create_file_formats >> snowflake_create_table_scores >> snowflake_create_table_stats >> snowflake_create_table_news >> snowflake_create_table_top_100_players_stats