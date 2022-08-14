
from concurrent.futures import ThreadPoolExecutor
import ffmpeg
import os
import logging
from queue import Queue
from logging import Logger
from . import Track

logger: Logger = logging.getLogger(__name__)


class TrackDownloader:
    def __init__(self, max_workers: int):
        self._max_workers = max_workers

    async def download_tracks(self, qtracks: "Queue[Track]", path: str):

        def download_track(track: Track):
            if not os.path.exists(f"{path}/{track.title.replace('/','')}.mp3") and track:
                logger.info(f'downloading {track.title} into {path}')
                (out, err) = (
                    ffmpeg.run
                    .input(track.url)
                    .output(f"{path}/{track.title.replace('/','')}.mp3")
                    .overwrite_output()
                    .run(capture_stdout = True, capture_stderr = True)
                )
                logger.info(out);
            else:
                logger.warning(f'file {path} already exist')

        try:
            with ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="ffmpeg-download") as pool:

                while not qtracks.empty():
                    track = qtracks.get(timeout=1.0)

                    pool.submit(download_track, track)
                    qtracks.task_done()

        except ffmpeg.Error as err:
            logger.error('ffmpeg Error', exc_info=1)
