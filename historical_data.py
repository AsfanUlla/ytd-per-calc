import pandas as pd
from pathlib import Path
import gc

from config import CACHE_FOLDER, TICKER_LIST_URLS
# from downloader import Downloader

import yfinance as yf

#Macrotrends api
MACROTRENDS_API = 'https://www.macrotrends.net/assets/php/stock_data_download.php?t={}'

class HistoricalData:

    def __init__(self, api=MACROTRENDS_API) -> None:
        self.api = api

    @staticmethod
    def _chunks(lst, n=500):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def _fix_ticker(symbol: str) -> str:
        symbol = symbol.strip()

        # Convert symbols to yFinance format
        symbol = symbol.replace("/", "-") # Class Shares

        # Preferred shares
        if "^" in symbol:
            base, suffix = symbol.split("^", 1)

            # If suffix empty (e.g., "TFIN^"), return base ticker
            if not suffix:
                return base.strip()

            symbol = f"{base}-P{suffix}"

        # TODO - Filter special tickers

        return symbol


    def load_tickers(self, parquet_path: Path):
        df = pd.read_parquet(parquet_path)
        if df.empty:
            return None

        symbols = df.index.dropna().unique().astype(str).tolist()
        cleaned = [self._fix_ticker(sym) for sym in symbols]

        return cleaned

    # def build_download_urls(self, symbols: list):
    #     return {
    #         symbol: self.api.format(symbol)
    #         for symbol in symbols
    #     }

    async def download(self, exchange, tickers):
        output_file = None

        print(f"Downloading Historical data for {exchange.upper()} tickers")
        hist_df = yf.download(
            tickers,
            period='max',
            threads=True,
            group_by='ticker',
            auto_adjust=True
        )

        if hist_df is None or hist_df.empty:
            return output_file

        output_file = CACHE_FOLDER.joinpath(f"{exchange}_hist.parquet")
        hist_df.to_parquet(output_file, engine='pyarrow')

        # Lazy mem cleanup
        del hist_df
        gc.collect()

        return output_file

    async def download_all(self):

        # downloader = Downloader(
        #     initial_delay=1,
        #     backoff_factor=2,
        #     concurrency_limit=10
        # )

        hist_data_files = []

        for key in TICKER_LIST_URLS.keys():
            file = CACHE_FOLDER.joinpath(f"{key}.parquet")

            if not file.is_file():
                continue

            # Load symbols for this exchange
            tickers = self.load_tickers(file)

            if not tickers:
                continue

            output_file = await self.download(key, tickers)
            hist_data_files.append(output_file)
            print(f"{key.upper()} tickers historical data saved to - {output_file}")


            # build api urls with ticker
            # urls = self.build_download_urls(symbols)
            # print(f"\nDownloading {len(symbols)} symbols for {file.stem}...\n")
            # await downloader.run(urls, destination=CACHE_FOLDER.joinpath(file.stem))

        return hist_data_files
