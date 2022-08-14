import asyncio
from queue import Queue
import argparse

from . import initLogging
from .client import Client, Configurations
from .downloader import TrackDownloader
from .credentials import Credentials
from .selenium import SeleniumCredentialsProvider
from pathlib import Path

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__('SoundCloud Downloader')
        super().add_argument('-d', '--download-folder',
                            help='sepecifies downloading directory', default='./SoundCloud Downloads')
        super().add_argument('-l', '--likes', help='download profile likes', action='store_true')
        super().add_argument('-p', '--profile-username', required=True,
                            help='specifies profile username to target profile ex. https://soundcloud.com/\\{username\\}')
        super().add_argument(
            '--limit', help='specifies paging of track collections', default=200)
        super().add_argument('-f', '--first-page-only', help='download donload only first page', action='store_true')


async def main(config: Configurations):
    provider = SeleniumCredentialsProvider()

    
    credentials: Credentials = await provider.credentials(config.profile_username)

    sc_client: Client
    qtracks = Queue()
    async with Client(config) as sc_client:
        tracks = await sc_client.get_tracks(credentials)
        
    for track in tracks:
        qtracks.put(track)

    downloader = TrackDownloader(max_workers=config.max_workers)
    await downloader.download_tracks(qtracks, f'{Path.home()}/{config.download_folder}/{config.profile_username}')

if __name__ == '__main__':
    parser = ArgumentParser()

    initLogging()

    args = parser.parse_args()
    if args.likes:
        download_folder = f'{args.download_folder}/likes'
    config = Configurations(
        download_folder=args.download_folder,
        collection_type='track_likes',
        profile_username=args.profile_username,
        page_size=args.limit,
        first_page_only= args.first_page_only
    )

    asyncio.run(main(config=config))
