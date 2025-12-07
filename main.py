import ijson
from pathlib import Path
import asyncio
import pandas as pd

from downloader import Downloader
from historical_data import Historical
from utils import parquet_to_csv

from config import TICKER_LIST_FOLDER, TICKER_LIST_URLS, CACHE_FOLDER

def get_ticker_list():

    # Loop through each exchange screener data file
    for key in TICKER_LIST_URLS.keys():
        file = TICKER_LIST_FOLDER.joinpath(f"{key}.json")

        if file.is_file():
            # Construct initial table with fundamentals
            field_order = ["name", "marketCap", "industry", "summary"]
            # Structure: { row_key: {symbol: value} }
            table = {key: {} for key in field_order}

            with open(file, 'r') as f:
                # stream json array and extract all the symbols and fundamentals
                for row in ijson.items(f, "data.rows.item"):
                    # Symbols
                    symbol = row.get("symbol")

                    if not symbol:
                        continue

                    # Get fundamental data
                    name = row.get("name")
                    marketCap = row.get("marketCap")
                    industry = row.get("industry") or row.get("sector")

                    # Fill table
                    table["name"][symbol] = name
                    table["marketCap"][symbol] = marketCap
                    table["industry"][symbol] = industry

            # Create data frame with table
            # df = pd.DataFrame(table).T
            # df = df.reset_index()
            # df.rename(columns={"index": ""}, inplace=True)

            # # Cache the data frame
            # df.to_parquet(CACHE_FOLDER.joinpath(f"{key}.parquet"))
            # print(f"Initial table - {CACHE_FOLDER.joinpath(f"{key}.parquet")}")

            # Test
            # parquet_to_csv(CACHE_FOLDER.joinpath(f"{key}.parquet"), f"{key}_test.csv")
            #
            #


if __name__ == '__main__':
    CACHE_FOLDER.mkdir(parents=True, exist_ok=True)

    # Download Ticker list from Nasdaq Screener API
    # download_ticker_list = Downloader()
    # asyncio.run(download_ticker_list.run(TICKER_LIST_URLS, destination=TICKER_LIST_FOLDER))

    # # Ticker symbol extraction
    # get_ticker_list()

    # Historical data download
    asyncio.run(Historical().download_all())
