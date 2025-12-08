from pathlib import Path

DATA_FOLDER = Path('data')
CACHE_FOLDER = DATA_FOLDER.joinpath('cache')
TICKER_LIST_FOLDER = DATA_FOLDER.joinpath('ticker_list')

#NASDAQ screener api
NASDAQ_SCREENER_API = 'https://api.nasdaq.com/api/screener/stocks?exchange={}&download=true'

# NASDAQ company info api
NASDAQ_INFO_API = 'https://api.nasdaq.com/api/company/{}/company-profile'

#API to download listed tickers on NYSE, NASDAQ, AMEX
TICKER_LIST_URLS = dict(
    nyse=NASDAQ_SCREENER_API.format('NYSE'),
    nasdaq=NASDAQ_SCREENER_API.format('NASDAQ'),
    amex=NASDAQ_SCREENER_API.format('AMEX'),
)
