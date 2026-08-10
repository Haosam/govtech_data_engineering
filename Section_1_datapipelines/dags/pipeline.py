from datetime import datetime
from zoneinfo import ZoneInfo

from airflow.sdk import dag, task


@dag(
    dag_id="application_processing_hourly",

    # Run once every hour
    schedule="@hourly",

    start_date=datetime(
        2026,
        8,
        10,
        tzinfo=ZoneInfo("Asia/Singapore"),
    ),

    # Do not backfill historical hourly runs
    catchup=False,

    tags=["applications", "etl"],
)
def application_processing_hourly():

    @task
    def process_applications_task():

        from application_etl import (
            process_incoming_folder
        )

        process_incoming_folder()

    process_applications_task()


application_processing_hourly()