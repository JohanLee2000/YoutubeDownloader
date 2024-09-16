# YoutubeDownloader# YouTube Video to MP3 Downloader

A Python tool that downloads YouTube videos and playlists as `.mp3` files.

## Features
- Download YouTube videos and playlists
- Convert downloaded videos to MP3 format

## Requirements
- Python 3.x
- `yt-dlp` and `moviepy` libraries
- ffmpeg installed and in PATH environment variable (or specify path in download_video_as_mp3: 'ffmpeg_location')

## Setup
1. Clone the repo:
    ```bash
    git clone https://github.com/JohanLee2000/YoutubeDownloader.git
    cd youtube-downloader
    ```

2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the script:
    ```bash
    python src/main.py
    ```

4. Enter the YouTube URL:
    ```bash
    {URL}
    ```
    example: https://www.youtube.com/watch?v=8wWbYuYGT1k

5. Enter the output directory (where you want to store the downloaded files):
    ```bash
    {Path}
    ```
    example: Music

    It will then put the file inside the existing directory or create one if not.

## License
MIT License
