import re
import os
import string
import requests
import argparse
import time

from osu import Client, UserScoreType
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "beatmaps"
)

if not os.path.exists(DEFAULT_OUTPUT_DIR):
    os.makedirs(DEFAULT_OUTPUT_DIR)

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
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c if c in valid_chars else "_" for c in filename)


def parse_args():
    parser = argparse.ArgumentParser(description="osu! Download Hub CLI")
    parser.add_argument("--username", required=True, help="osu! username")
    parser.add_argument("--top-plays", type=int, help="Number of top plays to download")
    parser.add_argument(
        "--maps-type",
        help="Type of maps to download(favourite, graveyard, loved, most_played, pending, ranked, guest)",
    )
    parser.add_argument("--maps-amount", type=int, help="Number of maps to download")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for downloaded files",
    )

    return parser.parse_args()


def download_file(url, path):
    response = requests.get(url, stream=True)
    total_length = int(response.headers.get("content-length"))
    downloaded_length = 0
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
            downloaded_length += len(chunk)
            print(
                f"Downloading: {downloaded_length / total_length * 100:.2f}% complete",
                end="\r",
            )
    print("\nDownload Done!")


def download_beatmaps(beatmaps, output_dir):
    for beatmap_id in beatmaps:
        response = requests.get(f"https://api.chimu.moe/v1/set/{beatmap_id}")
        response.raise_for_status()

        data = response.json()
        map_name = get_map_name(data)
        full_path = os.path.join(output_dir, f"{map_name}.osz")

        print(f"Downloading: {map_name}.osz")
        download_url = f"https://api.chimu.moe/v1/download/{beatmap_id}"
        download_file(download_url, full_path)

    time.sleep(5)

def confirm_download(maps_amount):
    user_input = input(f"You are about to download {maps_amount} beatmaps, proceed? (Y/n): ").strip().lower()
    return user_input == 'y'

def get_user_top_plays(username, top_plays_count):
    beatmaps = [
        client.get_beatmap(score.beatmap_id).beatmapset_id
        for score in client.get_user_scores(
            client.get_user(user=username).id, UserScoreType.BEST, limit=top_plays_count
        )
    ]

    return beatmaps


def get_user_maps(username, maps_type, maps_amount):
    beatmaps = [
        beatmap.id
        for beatmap in client.get_user_beatmaps(
            client.get_user(user=username).id, maps_type, limit=maps_amount
        )
    ]

    return beatmaps


def get_map_name(data):
    map_name = re.sub(
        r'[<>:"/\\|?*]', "", sanitize_filename(f"{data['Artist']} - {data['Title']}")
    )

    return map_name

def main():
    args = parse_args()

    output_dir = args.output_dir
    username = args.username
    top_plays_count = args.top_plays
    download_plays = top_plays_count is not None
    maps_type = args.maps_type or None
    maps_amount = args.maps_amount or None
    download_maps = maps_type is not None

    if download_plays:
        beatmaps = get_user_top_plays(username, top_plays_count)
    elif download_maps:
        beatmaps = get_user_maps(username, maps_type, maps_amount)
    else:
        return
    
    if not confirm_download(len(beatmaps)):
        print("Download cancelled.")
        return

    download_beatmaps(beatmaps, output_dir)

if __name__ == "__main__":
    main()
