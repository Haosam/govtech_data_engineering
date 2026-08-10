from pathlib import Path

import pandas as pd

from dags.application_etl import process_applications


INPUT_FILE = Path(
    "./data/incoming/applications_dataset_2.csv"
)


df = pd.read_csv(
    INPUT_FILE,
    dtype={
        "name": "string",
        "email": "string",
        "date_of_birth": "string",
        "mobile_no": "string",
    },
)


success_df, failed_df = (
    process_applications(df)
)


success_df.to_csv(
    "./data/successful/"
    "successful_applications_2.csv",
    index=False,
)


failed_df.to_csv(
    "./data/failed/"
    "failed_applications_2.csv",
    index=False,
)


print(
    f"Successful applications: "
    f"{len(success_df)}"
)

print(
    f"Failed applications: "
    f"{len(failed_df)}"
)