import yt_dlp
import logging
import time
import os
import sys
from urllib.parse import urlparse, parse_qs

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def is_youtube_mix(playlist_id):
    """
    Checks if the playlist is a YouTube Mix based on the playlist ID.
    """
    return playlist_id.startswith('RD')  # YouTube Mixes usually have IDs starting with 'RD'

def extract_playlist_id(url):
    """
    Extracts the playlist ID from a URL if present and checks if it is a YouTube Mix.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    playlist_id = query_params.get('list', [None])[0]

    if playlist_id and is_youtube_mix(playlist_id):
        logging.info(f"Detected YouTube Mix: {playlist_id}")
    else:
        logging.info(f"Detected regular playlist: {playlist_id}")
    
    return playlist_id

def download_video_as_mp3(video_url, output_directory, progress_callback=None, max_retries=2, retry_delay=5):
    """
    Downloads a YouTube video as an MP3 file using yt-dlp.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if hasattr(sys, '_MEIPASS'):
                ffmpeg_location = os.path.join(sys._MEIPASS, 'ffmpeg.exe')  # Path to bundled ffmpeg
            else:
                ffmpeg_location = 'ffmpeg.exe'  # Fallback for when not bundled
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': ffmpeg_location,  # Specify path if not in PATH
                'progress_hooks': [lambda d: progress_hook(d, progress_callback)],  # Pass the progress callback
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information to get the title before downloading
                video_info = ydl.extract_info(video_url, download=False)
                video_title = video_info['title']

                ydl.download([video_url])
            
            logging.info(f"{video_title} - Download complete!")
            return

        except yt_dlp.DownloadError as e:
            logging.error(f"Error downloading video: {e}. Retrying in {retry_delay} seconds...")
        
        attempt += 1
        time.sleep(retry_delay)

    logging.error(f"Failed to download video after {max_retries} attempts.")

def download_playlist_as_mp3_concurrently(playlist_url, output_directory, progress_callback=None, max_retries=3, retry_delay=5):
    """
    Downloads all videos in a YouTube playlist as MP3 files concurrently using yt-dlp.
    """
    try:
        ydl_opts = {
            'extract_flat': True,  # Don't download the videos, just extract links
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            video_entries = playlist_info['entries']
        
        # Track progress and video titles
        for idx, video_entry in enumerate(video_entries):
            video_url = video_entry['url']
            video_title = video_entry['title']
            # Start downloading and pass the video title to the progress callback
            if callable(progress_callback):
                progress_callback(0, f"Downloading video {idx + 1}/{len(video_entries)}: {video_title}")
            logging.info(f"Downloading video {idx + 1}/{len(video_entries)}: {video_title}")
            
            download_video_as_mp3(video_url, output_directory, lambda progress: progress_callback(progress, video_title))
        
        if callable(progress_callback):
            progress_callback(100, "All videos downloaded successfully!")

    except Exception as e:
        logging.error(f"An error occurred while downloading playlist: {e}")


def download_video_or_playlist(url, output_directory, progress_callback=None):
    """
    Determines whether the URL is a single video or a playlist and starts the download.
    """
    playlist_id = extract_playlist_id(url)
    
    if playlist_id:
        if is_youtube_mix(playlist_id):
            logging.info("This is a YouTube Mix. Fetching videos...")
            # Handle mix-specific logic (such as using the JS console method you mentioned)
            download_youtube_mix_as_mp3(url, output_directory, progress_callback)
        else:
            logging.info("Fetching videos...")
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            download_playlist_as_mp3_concurrently(playlist_url, output_directory, progress_callback)
    else:
        download_video_as_mp3(url, output_directory, progress_callback)


def extract_video_urls_from_mix(mix_url):
    """
    Extracts video URLs from a YouTube Mix.
    """
    ydl_opts = {
        'extract_flat': True,  # Don't download the videos, just extract links
        'playlist_items': '1-25',  # To extract all items in the playlist
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(mix_url, download=False)
            video_entries = playlist_info['entries']
            # video_urls = [entry['url'] for entry in video_entries if entry.get('url')]
            # print(video_entries)
            # return video_urls
            return video_entries

    except Exception as e:
        logging.error(f"An error occurred while extracting video URLs from the mix: {e}")
        return []

def download_youtube_mix_as_mp3(mix_url, output_directory, progress_callback=None):
    """
    Downloads all videos in a YouTube mix as MP3 files.
    """
    video_entries = extract_video_urls_from_mix(mix_url)
    if not video_entries:
        logging.error("No video entries found.")
        return

    for idx, video_entry in enumerate(video_entries):
        video_url = video_entry['url']
        video_title = video_entry['title']
        if callable(progress_callback):
            progress_callback(0, f"Downloading video {idx + 1}/{len(video_entries)}: {video_title}")

        download_video_as_mp3(video_url, output_directory, lambda progress: progress_callback(progress, video_title))

    if callable(progress_callback):
        progress_callback(100, "All videos downloaded successfully!")

def progress_hook(d, progress_callback=None):
    """
    Hook to display download progress and update UI if progress_callback is provided.
    """
    if d['status'] == 'downloading':
        total_size = d.get('total_bytes', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total_size > 0:
            progress = (downloaded / total_size) * 100
            if callable(progress_callback):
                progress_callback(progress)
    elif d['status'] == 'finished':
        logging.info("Converting file to mp3...")
        # Set progress to 100 when done
        if callable(progress_callback):
            progress_callback(100)
