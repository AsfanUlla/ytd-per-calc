import pandas as pd
from pathlib import Path
import gc
from datetime import datetime

from config import CACHE_FOLDER, DATA_FOLDER, TICKER_LIST_URLS
# from downloader import Downloader

import yfinance as yf

#Macrotrends api
MACROTRENDS_API = 'https://www.macrotrends.net/assets/php/stock_data_download.php?t={}'


def calculate_ytd_returns(df, exchange):

    print("\nCalulating returns YEAR-YTD (YTD=current date)")

    # Ensure datetime index
    df.index = pd.to_datetime(df.index)

    # Extract only Close prices
    close_df = df.xs("Close", axis=1, level=1).ffill()

    # Determine years to compute
    start_year = close_df.index.year.min()
    end_year = datetime.now().year
    years = range(start_year, end_year + 1)

    # Final (latest) price per ticker
    final_price = close_df.iloc[-1]
    final_price = pd.to_numeric(final_price, errors="coerce")

    results = pd.DataFrame(index=close_df.columns)

    for year in years:
        cutoff_date = pd.Timestamp(year, 1, 1) - pd.Timedelta(days=1)

        valid_data = close_df.loc[close_df.index <= cutoff_date]

        if not valid_data.empty:
            initial_price = valid_data.iloc[-1]
        else:
            initial_price = pd.Series([None] * len(close_df.columns), index=close_df.columns)

        # Ensure numeric
        initial_price = pd.to_numeric(initial_price, errors="coerce")

        # Vectorized YTD calculation
        ytd = ((final_price - initial_price) / initial_price) * 100
        ytd = ytd.astype(float).round(2)

        results[f"{year}-TD (%)"] = ytd

    # Remove empty columns (years with no data)
    results = results.dropna(how="all", axis=1)

    # Merge initial table results df
    initial_df = pd.read_parquet(CACHE_FOLDER.joinpath(f"{exchange}.parquet"))
    merge_df = initial_df.merge(results, on="Ticker", how="outer")

    print("\nWriting to file:")
    try:
        merge_df.to_excel(DATA_FOLDER.joinpath(f"{exchange}.xlsx"), engine='openpyxl')
        print(f"\nSuccessfully saved data {exchange.upper()} tickers to {DATA_FOLDER.joinpath(f"{exchange}.xlsx")}")
    except Exception as e:
        print(f"Failed to export to Excel: {e}")
    # print(f"Saving CSV to: {DATA_FOLDER.joinpath(f"{exchange}.csv")}")
    # merge_df.to_csv(DATA_FOLDER.joinpath(f"{exchange}.csv"))

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

        print(f"\nDownloading Historical data for {exchange.upper()} tickers")
        hist_df = yf.download(
            tickers,
            period='max',
            threads=True,
            group_by='ticker',
            auto_adjust=True
        )

        if hist_df is None or hist_df.empty:
            return output_file

        calculate_ytd_returns(hist_df, exchange)
        # output_file = CACHE_FOLDER.joinpath(f"{exchange}_hist.parquet")
        # hist_df.to_parquet(output_file, engine='pyarrow')

        # Lazy mem cleanup
        del hist_df
        gc.collect()

    async def download_all(self):

        # downloader = Downloader(
        #     initial_delay=1,
        #     backoff_factor=2,
        #     concurrency_limit=10
        # )
        # hist_data_files = []

        for key in TICKER_LIST_URLS.keys():
            file = CACHE_FOLDER.joinpath(f"{key}.parquet")

            if not file.is_file():
                continue

            # Load symbols for this exchange
            tickers = self.load_tickers(file)

            if tickers:
                await self.download(key, tickers)

            # build api urls with ticker
            # urls = self.build_download_urls(symbols)
            # print(f"\nDownloading {len(symbols)} symbols for {file.stem}...\n")
            # await downloader.run(urls, destination=CACHE_FOLDER.joinpath(file.stem))
