# Data Engineering Project: ETL and ELT using AWS, Airflow, DBT, Snowflake, Streamlit, Python, and SQL

This project demonstrates a comprehensive ETL (Extract, Transform, Load) and ELT (Extract, Load, Transform) pipeline, leveraging various tools and technologies to manage and process NBA data. The project showcases my expertise in data engineering and my ability to handle complex data workflows.

## Project Overview

The main objective of this project is to gather and process NBA scores, analyze the top 100 players of the 2024 season, the top 500 players of all time, and integrate NBA-related news using NewsAPI. The project involves:

- **ETL and ELT processes** using AWS, Airflow, and DBT
- **Data warehousing** with Snowflake
- **Interactive dashboards** created with Streamlit
- **Scripting and automation** with Python and SQL

## Tools and Technologies

- **AWS**: Cloud services for hosting and storage
- **Apache Airflow**: Workflow orchestration and scheduling
- **DBT (Data Build Tool)**: Data transformations
- **Snowflake**: Data warehousing
- **Streamlit**: Web application framework for data visualization
- **Python**: Scripting and automation
- **SQL**: Database management and querying
- **NewsAPI**: Integration of NBA-related news

## Project Structure

The project is organized as follows:

```
/project-root
|-- airflow
|   |-- dags
|   |-- plugins
|-- dbt
|   |-- models
|   |-- snapshots
|-- snowflake
|   |-- scripts
|-- streamlit
|   |-- app.py
|-- data
|   |-- raw
|   |-- processed
|-- scripts
|   |-- etl.py
|   |-- elt.py
|-- requirements.txt
|-- README.md
```

## Installation and Setup

### Prerequisites

- Python 3.x
- pip (Python package installer)
- AWS account
- Snowflake account
- API key for NewsAPI in .env file.

### Steps

1. **Clone the repository**:
    ```sh
    git clone https://github.com/BadreeshShetty/Data-Engineering-ELT-NBA-New-Stats
    cd your-repo-name
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Set up AWS credentials**:
    Configure your AWS CLI with the necessary credentials.
    ```sh
    aws configure
    ```

4. **Configure Snowflake connection**:
    Update the Snowflake credentials in Airflow.

5. **Run Airflow**:
    Set up and start the Airflow scheduler and webserver.
    ```sh
    airflow db init
    airflow scheduler
    airflow webserver
    ```

6. **Run DBT models**:
    Make changes in .dbt file for the project
    Navigate to the `dbt` directory and run the DBT models.
    ```sh
    dbt run
    ```


## Usage

1. **ETL and ELT processes**:
    - The ETL and ELT pipelines are managed by Airflow DAGs. You can trigger these pipelines from the Airflow web interface.

2. **Data Transformation**:
    - DBT models are used to transform the raw data stored in Snowflake.

3. **Data Visualization**:
    - The Streamlit app provides interactive dashboards to visualize the processed data and gain insights.

## Project Documentation

Detailed documentation of the project can be found [Data Engineering Project (ETL and ELT) (AWS, Airflow, DBT, Snowflake, Streamlit, Python, SQL)](https://grape-liquid-f37.notion.site/Data-Engineering-Project-ETL-and-ELT-AWS-Airflow-DBT-Snowflake-Streamlit-Python-SQL-14525b307afe4438bda2274903725ab5).

## Video Demonstration

https://youtu.be/lFwdFiiomzU
[https://github.com/BadreeshShetty/Data-Engineering-ELT-NBA-New-Stats/blob/main/Snowflake%20Top%20100%20Rank%202024.png](https://youtu.be/lFwdFiiomzU)


## Contact

For any questions or suggestions, feel free to reach out to me at [badreeshshetty@gmail.com].
