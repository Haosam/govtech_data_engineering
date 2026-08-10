from pathlib import Path
import hashlib

import pandas as pd


# ============================================================
# Configuration
# ============================================================

REFERENCE_DATE = pd.Timestamp("2022-01-01")

VALID_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

TITLE_PATTERN = (
    r"^(?:mr|mrs|ms|miss|dr|prof|sir|madam)\.?\s+"
)

CREDENTIAL_PATTERN = (
    r",?\s+(?:MD|DDS|PhD|DVM|DO)\.?\s*$"
)


# application_etl.py is inside /dags
# parent.parent therefore points to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASE_DIR = PROJECT_ROOT / "data"

INCOMING_DIR = BASE_DIR / "incoming"
SUCCESS_DIR = BASE_DIR / "successful"
FAILED_DIR = BASE_DIR / "failed"


# ============================================================
# Helper functions
# ============================================================

def clean_name(series: pd.Series) -> pd.Series:
    """
    Remove titles and professional credentials from names.
    """

    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(
            TITLE_PATTERN,
            "",
            regex=True,
            case=False,
        )
        .str.replace(
            CREDENTIAL_PATTERN,
            "",
            regex=True,
            case=False,
        )
        .str.strip()
    )


def parse_date(series: pd.Series) -> pd.Series:
    """
    Parse mixed date formats:
    YYYY-MM-DD
    YYYY/MM/DD
    DD-MM-YYYY
    DD/MM/YYYY
    """

    return pd.to_datetime(
        series.astype("string").str.strip(),
        format="mixed",
        dayfirst=True,
        errors="coerce",
    )


def calculate_age(dob: pd.Series) -> pd.Series:
    """
    Calculate age as of 1 Jan 2022.
    """

    age = (
        REFERENCE_DATE.year
        - dob.dt.year
        - (
            (REFERENCE_DATE.month < dob.dt.month)
            |
            (
                (REFERENCE_DATE.month == dob.dt.month)
                & (REFERENCE_DATE.day < dob.dt.day)
            )
        )
    )

    return age


def create_membership_id(row):
    """
    Format:
    <last_name>_<first 5 characters of SHA256(YYYYMMDD)>
    """

    dob_hash = hashlib.sha256(
        row["date_of_birth"].encode("utf-8")
    ).hexdigest()[:5]

    return f"{row['last_name']}_{dob_hash}"


# ============================================================
# Main transformation
# ============================================================

def process_applications(df: pd.DataFrame):

    df = df.copy()

    # --------------------------------------------------------
    # Standardise input
    # --------------------------------------------------------

    df["name_clean"] = clean_name(df["name"])

    df["parsed_dob"] = parse_date(
        df["date_of_birth"]
    )

    df["mobile_no"] = (
        df["mobile_no"]
        .astype("string")
        .str.strip()
    )

    df["email"] = (
        df["email"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Validation rules
    # --------------------------------------------------------

    # Missing name
    invalid_name = (
        df["name_clean"].isna()
        |
        df["name_clean"].str.strip().eq("")
    )

    # Mobile must be exactly 8 digits
    invalid_mobile = ~df["mobile_no"].str.fullmatch(
        r"\d{8}",
        na=False,
    )

    # DOB cannot be parsed
    invalid_dob = df["parsed_dob"].isna()

    # Must be at least 18 years old on 1 Jan 2022
    below_18 = (
        df["parsed_dob"]
        > pd.Timestamp("2004-01-01")
    )

    # Basic valid email structure:
    # something@something.something
    invalid_email = ~df["email"].str.fullmatch(
        VALID_EMAIL_PATTERN,
        case=False,
        na=False,
    )

    # --------------------------------------------------------
    # Failure reasons
    # --------------------------------------------------------

    df["failure_reason"] = ""

    df.loc[
        invalid_name,
        "failure_reason"
    ] += "missing_name;"

    df.loc[
        invalid_mobile,
        "failure_reason"
    ] += "invalid_mobile;"

    df.loc[
        invalid_dob,
        "failure_reason"
    ] += "invalid_date_of_birth;"

    df.loc[
        below_18,
        "failure_reason"
    ] += "below_18;"

    df.loc[
        invalid_email,
        "failure_reason"
    ] += "invalid_email;"

    failed_mask = (
        invalid_name
        | invalid_mobile
        | invalid_dob
        | below_18
        | invalid_email
    )

    # --------------------------------------------------------
    # Failed applications
    # --------------------------------------------------------

    failed_df = df.loc[failed_mask].copy()

    failed_df["failure_reason"] = (
        failed_df["failure_reason"]
        .str.rstrip(";")
    )

    # --------------------------------------------------------
    # Successful applications
    # --------------------------------------------------------

    success_df = df.loc[~failed_mask].copy()

    # Split name
    name_parts = (
        success_df["name_clean"]
        .str.split(n=1)
    )

    success_df["first_name"] = name_parts.str[0]
    success_df["last_name"] = name_parts.str[1]

    # Calculate age
    success_df["age_as_of_20220101"] = (
        calculate_age(
            success_df["parsed_dob"]
        )
    )

    # Above 18 field
    success_df["above_18"] = (
        success_df["age_as_of_20220101"] >= 18
    )

    # DOB -> YYYYMMDD
    success_df["date_of_birth"] = (
        success_df["parsed_dob"]
        .dt.strftime("%Y%m%d")
    )

    # Membership ID
    success_df["membership_id"] = (
        success_df.apply(
            create_membership_id,
            axis=1,
        )
    )

    # --------------------------------------------------------
    # Remove temporary columns
    # --------------------------------------------------------

    success_df = success_df.drop(
        columns=[
            "name_clean",
            "parsed_dob",
            "failure_reason",
            "age_as_of_20220101",
        ]
    )

    failed_df = failed_df.drop(
        columns=[
            "name_clean",
            "parsed_dob",
        ]
    )

    return success_df, failed_df


# ============================================================
# Folder processing for Airflow
# ============================================================

def process_incoming_folder():

    # Ensure directories exist
    for directory in [
        INCOMING_DIR,
        SUCCESS_DIR,
        FAILED_DIR,
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    csv_files = sorted(
        INCOMING_DIR.glob("*.csv")
    )

    print(
        f"Found {len(csv_files)} incoming CSV file(s)"
    )

    if not csv_files:
        print("No files to process.")
        return

    for csv_file in csv_files:

        print(
            f"Processing: {csv_file.name}"
        )

        success_path = (
            SUCCESS_DIR
            / f"{csv_file.stem}_successful.csv"
        )

        failed_path = (
            FAILED_DIR
            / f"{csv_file.stem}_failed.csv"
        )

        # Avoid processing an already completed file again
        if (
            success_path.exists()
            and failed_path.exists()
        ):
            print(
                f"Skipping already processed file: "
                f"{csv_file.name}"
            )
            continue

        # Read fields as strings so leading zeroes
        # in mobile numbers are preserved
        df = pd.read_csv(
            csv_file,
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
            success_path,
            index=False,
        )

        failed_df.to_csv(
            failed_path,
            index=False,
        )

        print(
            f"{csv_file.name}: "
            f"{len(success_df)} successful, "
            f"{len(failed_df)} failed"
        )