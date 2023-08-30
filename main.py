import re
import os
import string
import requests
import argparse
from osu import Client, UserScoreType
from dotenv import load_dotenv
import time

load_dotenv()

if not os.path.exists(".env"):
    print("Welcome to osu!")
    client_id = input("Enter your Client ID: ")
    client_secret = input("Enter your Client Secret: ")
    with open(".env", "w") as env_file:
        env_file.write(f"CLIENT_ID={client_id}\n")
        env_file.write(f"CLIENT_SECRET={client_secret}\n")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_url = None

client = Client.from_client_credentials(client_id, client_secret, redirect_url)


def sanitize_filename(filename):
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    return ''.join(c if c in valid_chars else '_' for c in filename)


def download_file(url, path):
    response = requests.get(url, stream=True)
    total_length = int(response.headers.get('content-length'))
    downloaded_length = 0
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                downloaded_length += len(chunk)
                print(
                    f"Downloading: {downloaded_length / total_length * 100:.2f}% complete", end="\r")
    print("\nDownload Done!")


def main():
    parser = argparse.ArgumentParser(description="osu! Download Hub CLI")
    parser.add_argument("--username", required=True, help="osu! username")
    parser.add_argument("--top-plays", type=int,
                        help="Number of top plays to download")
    parser.add_argument("--maps-type",
                        help="Type of maps to download(favourite, graveyard, loved, most_played, pending, ranked, guest)")
    parser.add_argument(
        "--maps-amount", type=int, help="Number of maps to download")
    parser.add_argument("--output-dir", default=os.path.dirname(os.path.abspath(__file__)),
                        help="Output directory for downloaded files")
    args = parser.parse_args()

    output_dir = args.output_dir
    username = args.username
    top_plays_count = args.top_plays
    download_plays = top_plays_count is not None
    maps_type = args.maps_type if args.maps_type else None
    maps_amount = args.maps_amount if args.maps_amount else None
    download_maps = maps_type is not None

    if download_plays or download_maps:
        if download_plays:
            user_id = client.get_user(user=username).id
            user_scores = client.get_user_scores(
                user_id, UserScoreType.BEST, limit=top_plays_count)
            beatmaps = [client.get_beatmap(
                score.beatmap_id).beatmapset_id for score in user_scores]
        elif download_maps:
            user_id = client.get_user(user=username).id
            user_beatmaps = client.get_user_beatmaps(
                user_id, maps_type, limit=maps_amount)
            beatmaps = [beatmap.id for beatmap in user_beatmaps]

        for beatmap_id in beatmaps:
            response = requests.get(
                f"https://api.chimu.moe/v1/set/{beatmap_id}")
            response.raise_for_status()

            data = response.json()
            artist = data["Artist"]
            title = data["Title"]
            map_name = f"{artist} - {title}"
            map_name = sanitize_filename(map_name)
            map_name = re.sub(r'[<>:"/\\|?*]', '', map_name)
            full_path = os.path.join(output_dir, f"{map_name}.osz")
            print(f"Downloading: {map_name}.osz")
            download_url = f"https://api.chimu.moe/v1/download/{beatmap_id}"
            download_file(download_url, full_path)

            time.sleep(5)


if __name__ == "__main__":
    main()
