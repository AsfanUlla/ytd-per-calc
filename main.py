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

            table = []

            with open(file, 'r') as f:
                # stream json array and extract all the symbols and fundamentals
                for row in ijson.items(f, "data.rows.item"):
                    # Symbols
                    symbol = row.get("symbol")

                    if not symbol:
                        continue

                    table.append(
                        dict(
                            Ticker=symbol,
                            Name=row.get("name", "NA"),
                            Industry=row.get("industry") or row.get("sector", "NA"),
                            MarketCap=row.get("marketCap", "NA"),
                            Summary="NA",
                        )
                    )

            if not table:
                continue

            df = pd.DataFrame(table)
            df.set_index("Ticker")
            # Cache the data frame
            df.to_parquet(CACHE_FOLDER.joinpath(f"{key}.parquet"))
            print(f"Initial table - {CACHE_FOLDER.joinpath(f"{key}.parquet")}")


if __name__ == '__main__':
    CACHE_FOLDER.mkdir(parents=True, exist_ok=True)

    # Download Ticker list from Nasdaq Screener API
    asyncio.run(Downloader().run(TICKER_LIST_URLS, destination=TICKER_LIST_FOLDER))

    # Ticker symbol extraction
    get_ticker_list()

    # Historical data download
    # asyncio.run(Historical().download_all())
