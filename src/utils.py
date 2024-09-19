import yt_dlp
import logging
import time
from urllib.parse import urlparse, parse_qs

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def extract_playlist_id(url):
    """
    Extracts the playlist ID from a URL if present.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('list', [None])[0]

def download_video_as_mp3(video_url, output_directory, progress_callback=None, max_retries=2, retry_delay=5):
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
            video_urls = [entry['url'] for entry in video_entries]
        
        # Track progress and video titles
        for idx, video_entry in enumerate(video_entries):
            video_url = video_entry['url']
            video_title = video_entry['title']
            # Start downloading and pass the video title to the progress callback
            if callable(progress_callback):
                progress_callback(0, f"Downloading video {idx + 1}/{len(video_entries)}: {video_title}")
            
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
        logging.info(f"Detected playlist ID: {playlist_id}")
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        download_playlist_as_mp3_concurrently(playlist_url, output_directory, progress_callback)
    else:
        download_video_as_mp3(url, output_directory, progress_callback)

def progress_hook(d, progress_callback=None):
    """
    Hook to display download progress and update UI if progress_callback is provided.
    """
    if d['status'] == 'downloading':
        total_size = d.get('total_bytes', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total_size > 0:
            progress = (downloaded / total_size) * 100
            logging.info(f"Downloading... {progress:.2f}%")
            if callable(progress_callback):
                progress_callback(progress)
    elif d['status'] == 'finished':
        logging.info("Download finished, now converting...")
        # Set progress to 100 when done
        if callable(progress_callback):
            progress_callback(100)
