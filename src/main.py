from utils import download_video_or_playlist

if __name__ == "__main__":
    url = input("Enter the YouTube URL: ")
    output_path = input("Enter the output directory: ")
    download_video_or_playlist(url, output_path)
