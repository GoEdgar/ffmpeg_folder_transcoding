import os
import time
import queue
import threading

import ffmpeg
import filetype

FFMPEG_PATH = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
MEDIA_FOLDER_PATH = r"E:\Фото и видео"
NEW_FOLDER_PREFIX = "re-encoded"
OUTPUT_VIDEO_CONTAINER = ".mp4"

ROOT_PATH_DEPTH = len(MEDIA_FOLDER_PATH.split(os.sep))
*ROOT_PATH, OLD_FOLDER_NAME = os.path.split(MEDIA_FOLDER_PATH)
NEW_FOLDER_NAME = "{} {}".format(OLD_FOLDER_NAME, NEW_FOLDER_PREFIX)
NEW_FOLDER_PATH = os.path.join(*ROOT_PATH, NEW_FOLDER_NAME)

WORK_QUEUE = queue.Queue()
_COUNTER = 0

def create_root_folder():
    if not os.path.exists(NEW_FOLDER_PATH):
        os.makedirs(NEW_FOLDER_PATH)


def generate_work_list():
    create_root_folder()
    for path, dirs, files in os.walk(MEDIA_FOLDER_PATH):
        relative_path = path.split(os.sep)[ROOT_PATH_DEPTH:]
        os.makedirs(os.path.join(NEW_FOLDER_PATH, *relative_path), exist_ok=True)
        for file in files:
            old_file_path = os.path.join(path, file)
            new_file_path = os.path.join(NEW_FOLDER_PATH, *relative_path, file)

            if not os.path.exists(new_file_path):
                WORK_QUEUE.put([old_file_path, new_file_path])


def is_video(path):
    file_type = filetype.guess(path)
    if file_type is None:
        return False
    return "video" in file_type.mime


def replace_file_extension(new_file):
    dot_ext_index = new_file.rfind('.')
    new_file = list(new_file)
    new_file[dot_ext_index:] = OUTPUT_VIDEO_CONTAINER
    return "".join(new_file)


def threaded_worker(codec):
    while not WORK_QUEUE.empty():
        old_file, new_file = WORK_QUEUE.get()
        if is_video(old_file):
            new_file = replace_file_extension(new_file)
            config = ffmpeg.input(old_file)
            config = ffmpeg.output(config, new_file,
                                   preset="slow",
                                   vcodec=codec,
                                   maxrate="3m",
                                   bufsize="10m")
            try:
                ffmpeg.run(config, cmd=FFMPEG_PATH, capture_stdout=True,
                           capture_stderr=True)
            except:
                print(old_file)
            else:
                global _COUNTER
                _COUNTER += 1
                print(_COUNTER, new_file)

        WORK_QUEUE.task_done()


generate_work_list()

for _ in range(3):
    threading.Thread(target=threaded_worker, args=("hevc_nvenc",)).start()



