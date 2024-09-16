import yt_dlp
import os
import logging
from tqdm import tqdm
import threading
import time
from urllib.parse import urlparse, parse_qs

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_playlist_id(url):
    """
    Extracts the playlist ID from a URL if present.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('list', [None])[0]

def download_video_as_mp3(video_url, output_directory, max_retries=2, retry_delay=5):
    """
    Downloads a YouTube video as an MP3 file using yt-dlp.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # 'ffmpeg_location': '/path/to/ffmpeg',  # Specify path if not in PATH
                'progress_hooks': [progress_hook],  # Add progress hook
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            logging.info("Download complete!")
            return

        except yt_dlp.DownloadError as e:
            logging.error(f"Error downloading video: {e}. Retrying in {retry_delay} seconds...")
        
        attempt += 1
        time.sleep(retry_delay)

    logging.error(f"Failed to download video after {max_retries} attempts.")

def download_playlist_as_mp3_concurrently(playlist_url, output_directory, max_retries=3, retry_delay=5):
    """
    Downloads all videos in a YouTube playlist as MP3 files concurrently using yt-dlp.
    """
    try:
        ydl_opts = {
            'extract_flat': True,  # Don't download the videos, just extract links
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            video_urls = [entry['url'] for entry in playlist_info['entries']]

        # Multithreading for concurrent downloads
        threads = []
        for video_url in video_urls:
            thread = threading.Thread(target=download_video_as_mp3, args=(video_url, output_directory, max_retries, retry_delay))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()  # Wait for all threads to finish
        
        logging.info("All videos in playlist downloaded successfully!")

    except Exception as e:
        logging.error(f"An error occurred while downloading playlist: {e}")

def download_video_or_playlist(url, output_directory):
    """
    Determines whether the URL is a single video or a playlist and starts the download.
    """
    playlist_id = extract_playlist_id(url)
    
    if playlist_id:
        logging.info(f"Detected playlist ID: {playlist_id}")
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        download_playlist_as_mp3_concurrently(playlist_url, output_directory)
    else:
        download_video_as_mp3(url, output_directory)

def progress_hook(d):
    """
    Hook to display download progress in the console using tqdm.
    """
    if d['status'] == 'downloading':
        # Update the progress bar with the downloaded bytes and total file size
        total_size = d.get('total_bytes', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total_size > 0:
            progress = (downloaded / total_size) * 100
            print(f"Progress: {progress:.2f}%")
    elif d['status'] == 'finished':
        print("Download finished, now converting...")
