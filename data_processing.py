import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import os

# GLOBAL 
EXCLUDED_BRANCHES = [
    50009,
    50011,
    50016,
    50018,
    50036,
    50037,
    50038,
    50046,
]

# Set up logger 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
)
file_handler = logging.FileHandler("logs.log")  # Create the file handler
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def load_branch_data(filename="branch_data.json"):
    """Loads branch data from a JSON file."""
    try:
        with open(filename, "r") as f:
            branch_data = json.load(f)
            logger.info(f"Branch data loaded from {filename}")
            return branch_data
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {filename}")
        return {}

def get_branch_name(branch_id, branch_data):
    """Returns the branch name for a given branch ID."""
    return branch_data.get(str(branch_id), "Unknown Branch")


def process_data(uploaded_file):
    """Processes uploaded Excel data and returns a DataFrame."""
    try:
        df = pd.read_excel(uploaded_file)
        # Handle empty DataFrame
        if df.empty:
            logger.warning("Uploaded Excel file is empty.")
            raise ValueError("Uploaded Excel file is empty.")  # Raise error for Streamlit
        logger.info("Excel file successfully loaded.")
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise

    try:
        df = df[df["Status"] == "Applied"][["Channel database", "Date uploaded"]]
        df["Date uploaded"] = pd.to_datetime(df["Date uploaded"])
        df_filtered = df.groupby(["Channel database"]).max()
        df_filtered = df_filtered.sort_values(by="Channel database", ascending=True)
        logger.info("Data filtered and grouped.")

    except Exception as e:
        logger.error(f"Error filtering and grouping data: {e}")
        raise

    try:
        now = datetime.now()
        time_diff = now - df_filtered["Date uploaded"]
        df_filtered["Time diff"] = (
            time_diff.astype(str).str.extract(r"(\d+:\d+:\d+)")[0]
        )
        logger.info("Time difference calculated.")
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        raise

    try:
        df_filtered["Branch ID"] = (df_filtered.index.str.extract(r"(\d+)")[0].astype(int).values)
        df_filtered["Branch ID"] = df_filtered["Branch ID"].astype(str)

        df_filtered.reset_index(inplace=True)
        df_filtered.drop("Channel database", axis=1, inplace=True)

        df_filtered = df_filtered.rename(columns={"Date uploaded": "Upload Date", "Time diff": "Time Difference"})
        logger.info("Branch ID extracted and DataFrame prepared.")

    except Exception as e:
        logger.error(f"Error extracting Branch ID and preparing DataFrame: {e}")
        raise

    return df_filtered


def check_missing_branches(results_df):
    """Analyzes branch status and returns a DataFrame with all branches."""

    results_df['Time Difference'] = pd.to_timedelta(results_df['Time Difference'])
    results_df["flag"] = results_df["Time Difference"].apply(lambda time_diff: 1 if time_diff > timedelta(minutes=30) else 0) 
    logger.info(f"Created flag")
    
    missed_df1 = results_df[results_df["flag"] ==1]
    logger.info("Apply condition1 (not outdates)")


    branch_data = load_branch_data()
    formatted_list = list(branch_data.keys()) 
    logger.info("Branch data loaded and filtered.")

    missed_branches = []
    for branch_id in formatted_list:  

        # Convert to list before creating the set
        if branch_id not in set(results_df["Branch ID"]) and branch_id not in EXCLUDED_BRANCHES:
            missed_branches.append(branch_id)

    logger.info("Apply condition2 (Branch in the file)")

    missed_df2 = pd.DataFrame(columns=missed_df1.columns.tolist())
    missed_df2["Branch ID"] = missed_branches
    
    missed_branches_df = pd.concat([missed_df1, missed_df2], axis=0)
    
    missed_branches_df = missed_branches_df[["Branch ID", "Upload Date", "Time Difference" ]]
    results_df = results_df[["Branch ID", "Upload Date", "Time Difference", "flag" ]]

    return results_df, missed_branches_df