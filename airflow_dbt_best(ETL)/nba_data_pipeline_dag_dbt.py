import logging
import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.utils.dates import days_ago
import pandas as pd
import requests
import json
import time
import os
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leagueleaders
from nba_api.live.nba.endpoints import scoreboard
from dotenv import load_dotenv

load_dotenv()

NBA_NEWS_API_KEY = os.getenv('NBA_NEWS_API_KEY')

# Constants
NBA_API_BASE_URL = 'https://newsapi.org/v2/everything'
S3_BUCKET = 'nba-stats-players'
SNOWFLAKE_STAGE = 'SNOW_S3_STAGE'
SNOWFLAKE_WAREHOUSE = 'NBA_STATS_WAREHOUSE'
SNOWFLAKE_DB = 'NBA_STATS_ANALYTICS'
SNOWFLAKE_SCHEMA = 'NBA_STATS'
DATA_FOLDER = '/home/ubuntu/dags/nba_news_stats_data'

# Ensure the data folder exists
os.makedirs(DATA_FOLDER, exist_ok=True)

# Define default arguments
default_args = {
    'owner': 'Airflow',
    'start_date': days_ago(2),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Initialize the DAG
dag = DAG(
    dag_id='nba_data_pipeline_dag',
    default_args=default_args,
    description='Fetch NBA data, upload to S3, and load into Snowflake',
    schedule_interval='@daily',
)

def fetch_nba_scores(**kwargs):
    games = scoreboard.ScoreBoard().get_dict()
    scores_list = []
    for game in games['scoreboard']['games']:
        game_details = {
            'game_id': game['gameId'],
            'home_team': game['homeTeam']['teamName'],
            'away_team': game['awayTeam']['teamName'],
            'home_score': game['homeTeam']['score'],
            'away_score': game['awayTeam']['score'],
            'home_best_player_name': game['gameLeaders']['homeLeaders']['name'],
            'home_best_player_points': game['gameLeaders']['homeLeaders']['points'],
            'home_best_player_rebounds': game['gameLeaders']['homeLeaders']['rebounds'],
            'home_best_player_assists': game['gameLeaders']['homeLeaders']['assists'],
            'away_best_player_name': game['gameLeaders']['awayLeaders']['name'],
            'away_best_player_points': game['gameLeaders']['awayLeaders']['points'],
            'away_best_player_rebounds': game['gameLeaders']['awayLeaders']['rebounds'],
            'away_best_player_assists': game['gameLeaders']['awayLeaders']['assists']
        }
        scores_list.append(game_details)

    scores_df = pd.DataFrame(scores_list)
    file_path = os.path.join(DATA_FOLDER, 'nba_scores.json')
    scores_df.to_json(file_path, orient='records')
    return file_path

def fetch_player_stats(**kwargs):
    seasons = [f"{year}-{str(year + 1)[-2:]}" for year in range(1984, 2023)]
    all_stats_df = pd.DataFrame()
    for season in seasons:
        season_leaders = leagueleaders.LeagueLeaders(season=season)
        season_leaders_df = season_leaders.get_data_frames()[0]
        season_leaders_df['SEASON'] = season
        all_stats_df = pd.concat([all_stats_df, season_leaders_df], ignore_index=True)
        time.sleep(1)

    player_stats = all_stats_df.groupby('PLAYER_ID').agg({
        'PLAYER': 'first',
        'TEAM': lambda x: ' + '.join(x.unique()),
        'PTS': 'sum',
        'GP': 'sum',
        'MIN': 'sum',
        'FGM': 'sum',
        'FGA': 'sum',
        'FG3M': 'sum',
        'FG3A': 'sum',
        'FTM': 'sum',
        'FTA': 'sum',
        'OREB': 'sum',
        'DREB': 'sum',
        'REB': 'sum',
        'AST': 'sum',
        'STL': 'sum',
        'BLK': 'sum',
        'TOV': 'sum',
        'PF': 'sum'
    }).reset_index()

    player_stats['PPG'] = player_stats['PTS'] / player_stats['GP']
    player_stats['APG'] = player_stats['AST'] / player_stats['GP']
    player_stats['RPG'] = player_stats['REB'] / player_stats['GP']
    player_stats['BPG'] = player_stats['BLK'] / player_stats['GP']
    player_stats['SPG'] = player_stats['STL'] / player_stats['GP']
    player_stats['FG%'] = player_stats['FGM'] / player_stats['FGA']
    player_stats['3P%'] = player_stats['FG3M'] / player_stats['FG3A']
    player_stats['FT%'] = player_stats['FTM'] / player_stats['FTA']

    player_stats.rename(columns={
        'FG%': 'FG_PERCENT',
        '3P%': 'FG3_PERCENT',
        'FT%': 'FT_PERCENT'
    }, inplace=True)

    top_500_players = player_stats.sort_values(by='PTS', ascending=False).head(500)
    columns = ["PLAYER_ID", "PLAYER", "TEAM", "GP", "MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA",
               "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PPG", "APG", "RPG",
               "BPG", "SPG", "FG_PERCENT", "FG3_PERCENT", "FT_PERCENT"]
    top_player_stats = top_500_players[columns]

    file_path = os.path.join(DATA_FOLDER, 'player_stats.csv')
    top_player_stats.to_csv(file_path, index=False)
    return file_path

def fetch_news(**kwargs):
    today = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    params = {
        'q': 'NBA',
        'from': start_date,
        'to': today,
        'sortBy': 'popularity',
        'apiKey': NBA_NEWS_API_KEY,
        'language': 'en'
    }

    response = requests.get(NBA_API_BASE_URL, params=params)
    news_data = response.json()
    articles = news_data.get('articles', [])

    news_list = []
    for article in articles:
        content = article.get('content', 'None')
        if content and len(content) > 200:
            content = content[:199]
            last_dot = content.rfind('.')
            content = content[:last_dot] if last_dot != -1 else content

        news_list.append({
            'title': article.get('title'),
            'description': article.get('description'),
            'url': article.get('url'),
            'news_source': article.get('source', {}).get('name'),
            'published_at': article.get('publishedAt'),
            'author': article.get('author'),
            'content': content
        })

    news_df = pd.DataFrame(news_list)
    news_df = news_df.drop_duplicates()
    file_path = os.path.join(DATA_FOLDER, 'nba_news.parquet')
    news_df.to_parquet(file_path)
    return file_path

def fetch_top_100_players_stats(**kwargs):
    top_100 = leagueleaders.LeagueLeaders(
        season='2023-24',
        season_type_all_star='Regular Season',
        stat_category_abbreviation='PTS'
    ).get_data_frames()[0][:100]

    # Feature-engineered variables
    top_100['PPG'] = top_100['PTS'] / top_100['GP']
    top_100['APG'] = top_100['AST'] / top_100['GP']
    top_100['RPG'] = top_100['REB'] / top_100['GP']
    top_100['BPG'] = top_100['BLK'] / top_100['GP']
    top_100['SPG'] = top_100['STL'] / top_100['GP']
    top_100['FG%'] = top_100['FGM'] / top_100['FGA']
    top_100['3P%'] = top_100['FG3M'] / top_100['FG3A']
    top_100['FT%'] = top_100['FTM'] / top_100['FTA']

    top_100.rename(columns={
        'FG%': 'FG_PERCENT',
        '3P%': 'FG3_PERCENT',
        'FT%': 'FT_PERCENT'
    }, inplace=True)

    # Sort players by total points scored
    top_100_players = top_100.sort_values(by='PTS', ascending=False)

    columns = ["PLAYER_ID", "RANK", "PLAYER", "TEAM", "GP", "MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA",
               "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PPG", "APG", "RPG",
               "BPG", "SPG", "FG_PERCENT", "FG3_PERCENT", "FT_PERCENT"]
    top_100_players_stats = top_100_players[columns]
    file_path = os.path.join(DATA_FOLDER, 'player_stats_2023_2024.json')
    top_100_players_stats.to_json(file_path, orient='records')
    return file_path

def upload_to_s3(file_path, s3_key):
    import boto3
    s3 = boto3.client('s3')
    s3.upload_file(file_path, S3_BUCKET, s3_key)
    return f's3://{S3_BUCKET}/{s3_key}'

with dag:
    fetch_nba_scores_task = PythonOperator(
        task_id='fetch_nba_scores',
        python_callable=fetch_nba_scores,
        provide_context=True,
    )

    fetch_player_stats_task = PythonOperator(
        task_id='fetch_player_stats',
        python_callable=fetch_player_stats,
        provide_context=True,
    )

    fetch_news_task = PythonOperator(
        task_id='fetch_news',
        python_callable=fetch_news,
        provide_context=True,
    )

    fetch_top_100_players_stats_task = PythonOperator(
        task_id='fetch_top_100_players_stats',
        python_callable=fetch_top_100_players_stats,
        provide_context=True,
    )

    upload_scores_to_s3_task = PythonOperator(
        task_id='upload_scores_to_s3',
        python_callable=upload_to_s3,
        op_kwargs={'file_path': f'{DATA_FOLDER}/nba_scores.json', 's3_key': 'nba_scores.json'},
        provide_context=True,
    )

    upload_stats_to_s3_task = PythonOperator(
        task_id='upload_stats_to_s3',
        python_callable=upload_to_s3,
        op_kwargs={'file_path': f'{DATA_FOLDER}/player_stats.csv', 's3_key': 'player_stats.csv'},
        provide_context=True,
    )

    upload_news_to_s3_task = PythonOperator(
        task_id='upload_news_to_s3',
        python_callable=upload_to_s3,
        op_kwargs={'file_path': f'{DATA_FOLDER}/nba_news.parquet', 's3_key': 'nba_news.parquet'},
        provide_context=True,
    )

    upload_top_100_stats_to_s3_task = PythonOperator(
        task_id='upload_top_100_stats_to_s3',
        python_callable=upload_to_s3,
        op_kwargs={'file_path': f'{DATA_FOLDER}/player_stats_2023_2024.json', 's3_key': 'player_stats_2023_2024.json'},
        provide_context=True,
    )

    snowflake_copy_scores = SQLExecuteQueryOperator(
        task_id='snowflake_copy_scores',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        COPY INTO {SNOWFLAKE_SCHEMA}.nba_scores
        FROM (
        SELECT 
            $1:game_id::STRING AS game_id,
            $1:home_team::STRING AS home_team,
            $1:away_team::STRING AS away_team,
            $1:home_score::INT AS home_score,
            $1:away_score::INT AS away_score,
            $1:home_best_player_name::STRING AS home_best_player_name,
            $1:home_best_player_points::NUMBER AS home_best_player_points,
            $1:home_best_player_rebounds::NUMBER AS home_best_player_rebounds,
            $1:home_best_player_assists::NUMBER AS home_best_player_assists,
            $1:away_best_player_name::STRING AS away_best_player_name,
            $1:away_best_player_points::NUMBER AS away_best_player_points,
            $1:away_best_player_rebounds::NUMBER AS away_best_player_rebounds,
            $1:away_best_player_assists::NUMBER AS away_best_player_assists
        FROM @{SNOWFLAKE_STAGE}/nba_scores.json)
        FILE_FORMAT = (FORMAT_NAME = 'JSON_FORMAT');
        """,
        conn_id='snowflake_conn',
    )

    snowflake_copy_stats = SQLExecuteQueryOperator(
        task_id='snowflake_copy_stats',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        COPY INTO {SNOWFLAKE_SCHEMA}.player_stats
        FROM @{SNOWFLAKE_STAGE}/player_stats.csv
        FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT');
        """,
        conn_id='snowflake_conn',
    )

    snowflake_copy_news = SQLExecuteQueryOperator(
        task_id='snowflake_copy_news',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        COPY INTO {SNOWFLAKE_SCHEMA}.nba_news
        FROM @{SNOWFLAKE_STAGE}/nba_news.parquet
        FILE_FORMAT = (FORMAT_NAME = 'PARQUET_FORMAT')
        MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
        """,
        conn_id='snowflake_conn',
    )

    snowflake_copy_top_100_stats = SQLExecuteQueryOperator(
        task_id='snowflake_copy_top_100_stats',
        sql=f"""
        USE WAREHOUSE {SNOWFLAKE_WAREHOUSE};
        USE {SNOWFLAKE_DB};
        COPY INTO {SNOWFLAKE_SCHEMA}.top_100_players_stats
        FROM (
        SELECT
            $1:PLAYER_ID::STRING AS PLAYER_ID,
            $1:RANK::NUMBER AS RANK,
            $1:PLAYER::STRING AS PLAYER,
            $1:TEAM::STRING AS TEAM,
            $1:GP::NUMBER AS GP,
            $1:MIN::NUMBER AS MIN,
            $1:FGM::NUMBER AS FGM,
            $1:FGA::NUMBER AS FGA,
            $1:FG3M::NUMBER AS FG3M,
            $1:FG3A::NUMBER AS FG3A,
            $1:FTM::NUMBER AS FTM,
            $1:FTA::NUMBER AS FTA,
            $1:OREB::NUMBER AS OREB,
            $1:DREB::NUMBER AS DREB,
            $1:REB::NUMBER AS REB,
            $1:AST::NUMBER AS AST,
            $1:STL::NUMBER AS STL,
            $1:BLK::NUMBER AS BLK,
            $1:TOV::NUMBER AS TOV,
            $1:PF::NUMBER AS PF,
            $1:PTS::NUMBER AS PTS,
            $1:PPG::NUMBER AS PPG,
            $1:APG::NUMBER AS APG,
            $1:RPG::NUMBER AS RPG,
            $1:BPG::NUMBER AS BPG,
            $1:SPG::NUMBER AS SPG,
            $1:FG_PERCENT::NUMBER AS FG_PERCENT,
            $1:FG3_PERCENT::NUMBER AS FG3_PERCENT,
            $1:FT_PERCENT::NUMBER AS FT_PERCENT
        FROM @{SNOWFLAKE_STAGE}/player_stats_2023_2024.json)
        FILE_FORMAT = (FORMAT_NAME = 'JSON_FORMAT');
        """,
        conn_id='snowflake_conn',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /home/ubuntu/nba_project && dbt run',
        dag=dag,
    )

# Define task dependencies
fetch_nba_scores_task >> upload_scores_to_s3_task >> snowflake_copy_scores
fetch_player_stats_task >> upload_stats_to_s3_task >> snowflake_copy_stats
fetch_news_task >> upload_news_to_s3_task >> snowflake_copy_news
fetch_top_100_players_stats_task >> upload_top_100_stats_to_s3_task >> snowflake_copy_top_100_stats

# dbt transformation after all Snowflake loads
[snowflake_copy_scores, snowflake_copy_stats, snowflake_copy_news, snowflake_copy_top_100_stats] >> dbt_run
