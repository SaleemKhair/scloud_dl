
import asyncio
from queue import Queue
import argparse

from . import initLogging
from .sc_client import SCClient, Configurations
from .track_downloader import TrackDownloader
from .credentials_provider import SeleniumCredentialsProvider, Credentials


async def main(config: Configurations):

    provider = SeleniumCredentialsProvider()
    task = asyncio.create_task(provider.get_credentials('zzool'))
    credentials: Credentials = await asyncio.ensure_future(task)

    config.credentials = credentials
    sc_client: SCClient
    async with SCClient(config) as sc_client:
        tracks = await sc_client.get_tracks()

    qtracks = Queue()
    for track in tracks:
        qtracks.put(track)

    downloader = TrackDownloader(max_workers=config.max_workers)
    await downloader.download_tracks(qtracks, './downloads')

if __name__ == '__main__':
    parser = argparse.ArgumentParser('SoundCloud Downloader')
    parser.add_argument('-d', '--download-folder',
                        help='sepecifies downloading directory')
    parser.add_argument('-l', '--likes', help='download profile likes')
    parser.add_argument('-p', '--profile-username',
                        help='specifies profile username to target profile ex. https://soundcloud.com/\\{username\\}')
    parser.add_argument('--limit', help='specifies paging of track collections')

    initLogging()

    args = parser.parse_args()

    config = Configurations(
        download_folder= args.download_folder,
        profile_username= args.profile_username,
        page_size= args.limit
    )

    asyncio.run(main(config=config))