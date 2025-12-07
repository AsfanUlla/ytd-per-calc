import asyncio
from typing import Dict
import aiohttp
import aiofiles
from pathlib import Path
from fake_useragent import UserAgent
from datetime import datetime
import random

from aiohttp.client_middlewares import ClientHandlerType
from aiohttp.client import ClientRequest, ClientResponse

from config import DATA_FOLDER

class Downloader(object):

    def __init__(self, initial_delay=0.5, retries=3, backoff_factor=1.2, concurrency_limit=25, **kwargs):
        self.initial_delay = initial_delay
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.semaphore = asyncio.Semaphore(concurrency_limit)

        self._keys = set()
        for k, v in kwargs.items():
            setattr(self, k, v)
            self._keys.add(k)


    async def retry_middleware(self,
        req: ClientRequest, handler: ClientHandlerType
    ) -> ClientResponse:
        for attempt in range(self.retries + 1):  # Try up to 3 times
            resp = await handler(req)

            # Return responce on success
            if resp.ok:
                return resp

            # If max attempts reached, return last response
            if attempt == self.retries:
                print(f"❌ Giving up after {self.retries} retries for {req.url}")
                return resp

            # Priority: server-specified retry time
            wait_time = resp.headers.get("Retry-After")

            if not wait_time:
                # exponential backoff
                wait_time = self.backoff_factor * (2 ** attempt)

                # Add jitter: ±20%
                jitter_multiplier = random.uniform(0.8, 1.2)
                wait_time *= jitter_multiplier

            print(f"Status: {resp.status}. Retrying in {wait_time:.2f} s. (attempt {attempt + 1}/{self.retries})...")

            # Close response
            resp.release()

            await asyncio.sleep(float(wait_time))

        return resp

    async def fetch_data(self, session, url, filepath):

        headers = {"User-Agent": UserAgent().random}
        await asyncio.sleep(self.initial_delay)

        async with self.semaphore:
            async with session.get(url, headers=headers) as response:

                # Get file extention from content-type header
                ext = "csv"
                if response.headers.get("content-type"):
                    ext = response.headers.get(
                        "content-type"
                    ).split(';')[0].split('/')[1].strip().lower()

                filepath = f"{filepath}.{ext}"

                # Read the response content in chunks and write to file
                async with aiofiles.open(filepath, mode="wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                print(f"\nDownload saved to {filepath}")

                return dict(
                    url=url,
                    success=response.ok,
                    status=response.status
                )

    async def run(self,
        urls:Dict,
        destination: Path = DATA_FOLDER,
    ):
        destination.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession(middlewares=(self.retry_middleware,), raise_for_status=True) as session:
            tasks = []
            for filename, url in urls.items():
                tasks.append(self.fetch_data(session, url, destination.joinpath(filename)))

            results = await asyncio.gather(*tasks)

            return results
