import pandas as pd
from pathlib import Path

from config import CACHE_FOLDER, TICKER_LIST_URLS
from downloader import Downloader

import yfinance as yf

#Macrotrends api
MACROTRENDS_API = 'https://www.macrotrends.net/assets/php/stock_data_download.php?t={}'

class Historical:

    def __init__(self, api=MACROTRENDS_API) -> None:
        self.api = api


    def load_tickers(self, parquet_path: Path):
        df = pd.read_parquet(parquet_path)
        return list(df.columns)[1:]  # skip first blank col

    def build_download_urls(self, symbols: list):
        return {
            symbol: self.api.format(symbol)
            for symbol in symbols
        }

    async def download_all(self):

        downloader = Downloader(
            initial_delay=1,
            backoff_factor=2,
            concurrency_limit=10
        )

        for key in TICKER_LIST_URLS.keys():
            file = CACHE_FOLDER.joinpath(f"{key}.parquet")

            if not file.is_file():
                continue

            # Load symbols for this exchange
            symbols = self.load_tickers(file)

            print("Fetching all historical data...")
            all_historical_data = yf.download(symbols, period='max', threads=True, group_by='ticker', auto_adjust=True)

            output_folder = CACHE_FOLDER.joinpath(file.stem)
            output_folder.mkdir(parents=True, exist_ok=True)

            if all_historical_data is not None:
                all_historical_data.to_parquet(output_folder.joinpath(f"{key}.parquet"))
                all_historical_data.to_csv(
                    output_folder.joinpath(f"{key}.csv"),
                )

            # build api urls with ticker
            # urls = self.build_download_urls(symbols)

            # print(f"\n📁 Downloading {len(symbols)} symbols for {file.stem}...\n")



            # await downloader.run(urls, destination=CACHE_FOLDER.joinpath(file.stem))

        print("\n🎯 ALL DONE!")
