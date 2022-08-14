
from aiohttp_retry import RetryClient, ExponentialRetry
import logging
import requests
from logging import Logger
import asyncio
from . import Track
from .credentials import Credentials
from typing import Set
from dataclasses import dataclass, field
import random
import aiofiles
import os
import csv
from aiocsv.writers import AsyncDictWriter
from aiocsv.readers import AsyncReader


logger: Logger = logging.getLogger(__name__)


@dataclass
class Configurations:
    profile_username: str
    download_folder: str
    collection_type: str

    retry_attempts: int = 4
    retry_start_timeout: float = 3
    retry_statuses: Set[int] = field(default_factory=lambda: set([403, 429]))
    base_url: str = "https://api-v2.soundcloud.com"
    first_page_only: bool = False
    page_size: int = 500
    max_workers: int = 6

class Client(RetryClient):
    def __init__(self, config: Configurations):
        super().__init__(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                attempts=config.retry_attempts,
                start_timeout=config.retry_start_timeout,
                statuses=config.retry_statuses
            ))
        self._cached_tracks: dict = {}
        if os.path.exists('./cache/tracks.tsv'):
            with open('./cache/tracks.tsv', 'r') as tracks_cache:
                reader = csv.DictReader(tracks_cache, fieldnames=["title", "url"], delimiter='\t')
                for row in reader:
                    self._cached_tracks[row['title']] = row['url']

        self._config: Configurations = config

    def _headers(self, credentials: Credentials):
        return {
            'Autherization': f'OAuth {credentials.oauth_token}',
            'Accept': 'application/json'
        }
    
    async def _get_collection(self, target, credentials: Credentials):

        resp = await self.get(
            url=target,
            headers=self._headers(credentials),
            params={
                'client_id': f'{credentials.client_id}',
                'limit': f'{self._config.page_size}',
                'linked_partitioning': 'true'
            })
        await asyncio.sleep(1)
        json_payload = await resp.json()
        return (json_payload['collection'], json_payload['next_href'])

    async def _from_json(self, json_track, credentials: Credentials) -> Track:
        track_title = json_track['title']
        if self._cached_tracks.get(track_title):
            logger.info(f'retrieving data for track: {track_title} from cache')
            return Track(title= track_title, url= self._cached_tracks[track_title])
        if len(json_track['media']['transcodings']) > 0:
            logger.info(f'retrieving data for {track_title} from soundcloud api')
            resp = await self.get(
                url=json_track['media']['transcodings'][0]['url'],
                params={'client_id': f'{credentials.client_id}'},
                headers=self._headers(credentials)
            )
            if resp.content_type == 'application/json':
                json_payload = await resp.json()
                track = Track(title=track_title, url=json_payload['url'])
                if json_payload.get('url'):
                    async with aiofiles.open('./cache/tracks.tsv', mode='a') as tracks_cache:
                        writer = AsyncDictWriter(tracks_cache, delimiter='\t', fieldnames=["title","url"])
                        await writer.writerow(track.__dict__)
                    return Track(title=json_track['title'], url=json_payload['url'])
        return None

    async def get_tracks(self, credentials: Credentials):
        """ Retrieve collection of tracks from api, based on collection_type """
        target = f"/users/{credentials.user_id}/{self._config.collection_type}"
        tasks = set()
        next_href = f'{self._config.base_url}{target}'
        logger.info(f'get collection url: {next_href}')
        async def _populate_tasks(href):
            (liked_collection, next_href) = await self._get_collection(href, credentials)
            for item in liked_collection:
                json_track = item['track']
                task = asyncio.create_task(self._from_json(json_track, credentials))
                tasks.add(task)
                await asyncio.sleep(random.uniform(0.05, 0.12))
            return next_href
        try:
            if self._config.first_page_only:
                await _populate_tasks(next_href)
            else:
                while next_href is not None:
                    next_href = await _populate_tasks(next_href)
        except TypeError:
            logger.error('problem', exc_info=2)
        except requests.exceptions.RetryError as ex:
            logger.error(
                'Problem with Auth, max retries exceeded!', exc_info=1)
            raise ex
        return await asyncio.gather(*tasks)