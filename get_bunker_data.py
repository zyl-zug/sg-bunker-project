"""
STEP 1 - Download Singapore's monthly bunker (ship fuel) sales.

Where the data comes from:
    MPA (Maritime and Port Authority of Singapore) publishes it on data.gov.sg.
    This script asks data.gov.sg for it through an "API" - a web address that
    hands back data instead of a web page. No manual download needed.

What it produces:
    data/bunker_sales_raw.csv            -> latest copy (other scripts read this)
    data/bunker_sales_raw_YYYYMMDD.csv   -> dated copy (so you can see revisions later)
"""

import os                      # reads settings on your computer (the API key) and makes folders
import time                    # lets the script pause, so we don't overload the server
from datetime import date      # today's date, used in the dated file name

import pandas as pd            # tables in Python, like Excel
import requests                # visits a web address and brings data back
from dotenv import load_dotenv # reads your secret key from the .env file

load_dotenv()  # opens .env (if it exists) and loads DATAGOV_API_KEY

# The dataset's ID number on data.gov.sg ("Bunker Sales Breakdown, Monthly")
DATASET_ID = "d_4f5abbf4486bf8e52bbed3be56dde562"
# The address every request goes to
URL = "https://data.gov.sg/api/action/datastore_search"
# Your "library card". Empty text if no key - it still works, just slower.
HEADERS = {"x-api-key": os.environ.get("DATAGOV_API_KEY", "")}


def fetch_all(resource_id, page_size=1000, retries=3):
    """
    The server hands out data in pages of up to 1,000 rows.
    This keeps asking for the next page until every row is collected.
    """
    rows, offset = [], 0           # rows = collected data; offset = where the next page starts
    while True:
        for attempt in range(retries):      # try up to 3 times per page
            r = requests.get(URL, headers=HEADERS, timeout=30,
                             params={"resource_id": resource_id,
                                     "limit": page_size, "offset": offset})
            # 429 = "too many requests", 5xx = server hiccup -> wait and try again
            if r.status_code in (429, 500, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()            # any other error -> stop and show it
            break
        else:
            raise RuntimeError(f"Failed after {retries} tries at row {offset}")

        result = r.json()["result"]         # turn the reply into Python data
        rows += result["records"]           # add this page's rows
        offset += page_size                 # move to the next page
        if offset >= result["total"]:       # got everything? stop
            break
        time.sleep(0.5)                     # short pause = polite to the server
    return pd.DataFrame(rows)               # turn the list of rows into a table


# This block only runs when you type "python get_bunker_data.py",
# not when another script borrows fetch_all().
if __name__ == "__main__":
    print("Key loaded:", HEADERS["x-api-key"] != "")
    df = fetch_all(DATASET_ID)
    print("Columns:", df.columns.tolist())
    print(df.head())                        # first 5 rows, as a quick check
    os.makedirs("data", exist_ok=True)      # create the data folder if missing
    df.to_csv("data/bunker_sales_raw.csv", index=False)
    df.to_csv(f"data/bunker_sales_raw_{date.today():%Y%m%d}.csv", index=False)
    print(f"Saved {len(df)} rows.")
