from discord.ext import commands
from googleapiclient.discovery import build
import spotipy
import json
import sqlite3
import requests


description = '''A bot for music sharing.'''
bot = commands.Bot(command_prefix='!', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def track(*details: str):
    """Gets a track from Spotify and YouTube."""
    try:
        if '-' in details:
            hyphen_index = details.index('-')
        elif '–' in details:
            hyphen_index = details.index('–')
        else:
            raise ValueError

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


@bot.command()
async def link(url: str):
    """Converts either a YouTube or Spotify URL."""
    if 'spotify' in url:
        track_name = get_spotify_track_name_from_url(url)
        track_name_list = track_name.split(' - ')
        artist = track_name_list[0]
        name = track_name_list[1]
        response = get_youtube_track(artist, name)

    elif ('youtube') in url or ('youtu.be' in url):
        track_name = get_youtube_track_name_from_url(url)
        response = search_spotify(track_name)
    await(bot.say(response))


@bot.command(pass_context=True)
async def npset(ctx, *lastfm_id):
    """Sets your Last.fm username. Must be done before !np can be used."""
    user_id = ctx.message.author.id
    lastfm_id = lastfm_id[0]

    update_db(user_id, lastfm_id)

    await(bot.say('Saved your Last.fm user ID as: ' + lastfm_id))


@bot.command(pass_context=True)
async def np(ctx):
    """Gets current/last scrobbled track from Last.fm."""
    user_id = ctx.message.author.id

    lastfm_id = get_user_from_db(user_id)

    if lastfm_id is None:
        await (bot.say('No Last.fm user name found. Use !npset to set your Last.fm user name'))
        return

    track = get_lastfm_now_playing(lastfm_id, 1)

    if track is None:
        await (bot.say('No now playing data found for Last.fm user :' + lastfm_id))
        return

    spotify_url = get_spotify_track(track[0], track[1])

    youtube_url = get_youtube_track(track[0], track[1])

    await (bot.say(spotify_url + '\n' + youtube_url))


@bot.command(pass_context=True)
async def nplast(ctx):
    """Gets second last scrobbled track from Last.fm."""
    user_id = ctx.message.author.id

    lastfm_id = get_user_from_db(user_id)

    if lastfm_id is None:
        await (bot.say('No Last.fm user name found. Use !npset to set your Last.fm user name'))
        return

    track = get_lastfm_now_playing(lastfm_id, 2)

    if track is None:
        await (bot.say('No now playing data found for Last.fm user :' + lastfm_id))
        return

    spotify_url = get_spotify_track(track[0], track[1])

    youtube_url = get_youtube_track(track[0], track[1])

    await (bot.say(spotify_url + '\n' + youtube_url))


def get_spotify_track(artist: str, name: str):
    try:
        search_str = artist + " " + name
        sp = spotipy.Spotify()
        result = sp.search(search_str, 1)
        track_url = result['tracks']['items'][0]['external_urls']['spotify']
    except IndexError:
        return "No Spotify match found. :("

    return track_url


def get_spotify_track_name_from_url(url: str):
    try:
        url_list = url.split('/')
        spotify_uri = 'spotify:track:' + url_list[-1]
        search_str = spotify_uri
        sp = spotipy.Spotify()
        result = sp.track(spotify_uri)

        track_name = result['artists'][0]['name'] + ' - ' + result['name']
    except IndexError:
        return "No Spotify match found. :("

    return track_name


def search_spotify(search: str):
    try:
        search_str = search
        sp = spotipy.Spotify()
        result = sp.search(search_str, 1)
        track_url = result['tracks']['items'][0]['external_urls']['spotify']
    except IndexError:
        return "No Spotify match found. :("

    return track_url


def get_youtube_track_name_from_url(url: str):
    DEVELOPER_KEY = youtube_token
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=url,
        part="id,snippet",
        maxResults=1
    ).execute()

    results = []

    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            results.append(search_result["snippet"]["title"])

    return results[0]


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


def get_lastfm_now_playing(lastfm_id, limit):
    parameters = {
        'user': lastfm_id,
        'api_key': lastfm_token,
        'limit': limit,
        'format': 'json'
    }

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks', params=parameters)

    result = r.json()

    if 'error' in result:
        return None

    artist = result['recenttracks']['track'][limit - 1]['artist']['#text']
    name = result['recenttracks']['track'][limit - 1]['name']

    track = (artist, name)

    return track


def initialise_db():
    db = sqlite3.connect('data.db')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, lastfm_name TEXT)
    ''')
    db.commit()


def update_db(user_id, lastfm_id):
    db = sqlite3.connect('data.db')
    cursor = db.cursor()
    cursor.execute('''INSERT OR REPLACE INTO users(id, lastfm_name)
                      VALUES(?,?)''', (user_id, lastfm_id))
    db.commit()


def get_user_from_db(user_id):
    db = sqlite3.connect('data.db')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM users WHERE id=?
                          ''', (user_id,))
    user = cursor.fetchone()
    if user is None:
        return None
    lastfm_id = user[1]
    return lastfm_id


with open('config.json', 'r') as f:
    config = json.load(f)

bot_token = config['BOT_TOKEN']

youtube_token = config['YOUTUBE_KEY']

lastfm_token = config['LASTFM_KEY']

initialise_db()

bot.run(bot_token)
