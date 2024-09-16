from utils import download_video_as_mp3, download_playlist_as_mp3_concurrently

if __name__ == "__main__":
    choice = input("Enter 'v' to download a video or 'p' to download a playlist: ").lower()
    url = input("Enter the YouTube URL: ")
    output_path = "./Music"

    if choice == 'v':
        download_video_as_mp3(url, output_path)
    elif choice == 'p':
        download_playlist_as_mp3_concurrently(url, output_path)
    else:
        print("Invalid choice. Please enter 'v' or 'p'.")
