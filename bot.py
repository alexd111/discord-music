from discord.ext import commands
from googleapiclient.discovery import build
import spotipy
import json


description = '''A music bot'''
bot = commands.Bot(command_prefix='?', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def track(*details: str):
    try:
        hyphen_index = details.index('-')
        if hyphen_index == 0 or hyphen_index == (len(details) - 1):
            raise ValueError
        artist = " ".join(details[:hyphen_index])
        name = " ".join(details[hyphen_index + 1:])

        response = get_spotify_track(artist, name)
        response = response + "\n" + get_youtube_track(artist, name)
    except ValueError:
        await bot.say('Format has to be: Artist - Song')
        return

    await bot.say(response)


def get_spotify_track(artist: str, name: str):
    search_str = artist + " " + name
    sp = spotipy.Spotify()
    result = sp.search(search_str, 1)
    return result['tracks']['items'][0]['external_urls']['spotify']


def get_youtube_track(artist: str, name: str):
    DEVELOPER_KEY = youtube_token
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=artist + " " + name,
        part="id,snippet",
        maxResults=1
    ).execute()

    results = []

    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            results.append('https://www.youtube.com/watch?v=' + search_result["id"]["videoId"])

    return results[0]


with open('config.json', 'r') as f:
    config = json.load(f)

bot_token = config['BOT_TOKEN']

youtube_token = config['YOUTUBE_KEY']

bot.run(bot_token)
