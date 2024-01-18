from __future__ import annotations

import asyncio
import datetime
import os
import random
from typing import Dict, List, Tuple
import subprocess
import requests
import eyed3
import discord

import yt_dlp
from discord.ext import commands
from moviepy.editor import *
from moviepy.editor import AudioFileClip
import traceback
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TRCK, TPOS, TPE2, TDRC

from botutils import *
from music_metadata_writer import apply_metadata
try:
    from .botutils import *
except:
    pass


download_song_cooldowns = {}
playlist_cooldowns = {}
cooldowns = {}

async def do_cooldown(user_id: int) -> None:
    cooldowns[user_id] = 1
    await asyncio.sleep(60)
    cooldowns[user_id] = 0

def get_playlist(user_id: int, playlist_id: int) -> Tuple[str, List[str]]:
    playlists=[pl.replace(".lpl", "") for pl in get_playlists(user_id)]
    name=""
    tracks=[]
    if not str(playlist_id) in playlists:
        return ("NOT FOUND", tracks)
    with open(f"users/user_{user_id}/playlists/{playlist_id}.lpl", "r", encoding="utf-8") as playlist_file:
        tracks=[line.strip() if not line.strip() == "" else None for line in playlist_file.readlines()]
        tracks.reverse()
        name=tracks.pop()
    return (name, tracks)

def get_playlists(user_id: int) -> List[str]:
    os.makedirs(f"users/user_{user_id}/playlists") if not os.path.exists(f"users/user_{user_id}/playlists") else None
    return [pl if pl.endswith(".lpl") else None for pl in os.listdir(f"users/user_{user_id}/playlists")]

def get_music():
    song_list = []
    for filename in os.listdir("musicmp3"):
        if filename.endswith(".mp3"):
            song_list.append(filename)
    return song_list

def search_songs(query_string: str):
    old_terms = query_string.lower().split(" ")
    terms = []
    for term in old_terms:
        if term not in terms:
            terms.append(term)
    matches = {}
    songs = get_music()
    for song in songs:
        matches[song] = 0
        for term in terms:
            if term in song.lower():
                matches[song] = matches[song] + 1
    ordered_songlist = []
    for i in range(1, 50):
        for song in matches:
            rank = int(matches[song])
            if rank == i:
                ordered_songlist.append(song)

    ordered_songlist.reverse()

    return ordered_songlist

class SongQueueObject():
    def __init__(self, query: str, user: discord.Member, download: bool = True):
        self.query: str = query
        self.user: discord.Member = user
        self.download: bool = download
        pass

class GuildVoiceClient():
    def __init__(self, queue: List[SongQueueObject] = [], channel: discord.TextChannel = None, user: discord.Member = None):
        self.queue: List[SongQueueObject] = queue
        self.text_channel: discord.TextChannel = channel
        self.current_user: discord.Member = user
        self.is_playing: bool = False
        self.loop: bool = False

ytdl_format_options = {
    'format': 'bestaudio/best',
    "outtmpl": "musicmp3/%(title)s.%(ext)s",
    'restrictfilenames': True,
    'nocheckcertificate': True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "2"
        }
    ],
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

async def update_git(filepath: str):
    return
    try:
        #folder_path = os.path.dirname(filepath)
        #os.chdir(folder_path)
        executable_path = r"C:\Program Files\Git\bin\git.exe"
        
        #if not os.path.exists('.git'):
        #    subprocess.run(['git', 'init'])
        
        if ".git" not in filepath:
            if os.path.getsize(filepath) / (1024 * 1024) < 100:
                subprocess.Popen([executable_path, 'add', filepath])
                #os.system(f'''{executable_path} add "{filepath}"''')
                subprocess.Popen([executable_path, 'commit', '-m', f'Committing {filepath}'])
                #os.system(f'''{executable_path} commit -m "Committing {filepath}"''')
                subprocess.Popen([executable_path, 'push', '-q', '-u', 'origin', 'main'])
                #os.system(f'''{executable_path} push -q -u origin main''')
    except:
        print("err updating git")

async def downloader(query: str):
    quer1 = query.replace(':', '')
    quer2 = quer1.replace('/', '')
    await wait()
    try:
        filename = await YTDLSource.to_file(query, ytdl=ytdl, loop=asyncio.get_event_loop())
        filename=filename.replace(".webm", ".mp3")
        apply_metadata("musicmp3/" + filename if not "musicmp3" in filename else filename)
        await update_git("musicmp3/" + filename if not "musicmp3" in filename else filename)
    except Exception as e1:
        print(f'An error occured: {e1} (code e1)')
    filename2=filename.replace('musicmp3\\', '')
    await wait()
    if not os.path.exists("musicmp3/" + filename2.replace(".mp3", ".mp4")):
        audio_clip=AudioFileClip("musicmp3/"+filename2)
        video_clip=VideoClip(lambda t: ImageClip('square.png').set_duration(audio_clip.duration).make_frame(t),duration=audio_clip.duration).set_audio(audio_clip)
        video_clip.write_videofile(filename=f"musicmp3/{filename2.replace('.mp3','.mp4')}",fps=1,codec='libx264',audio_codec='libmp3lame',threads=24,logger=None,ffmpeg_params=['-movflags','+faststart'])
        await update_git("musicmp3/" + filename2.replace(".mp3", ".mp4"))
    return filename2
    pass

class MusicBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            "outtmpl": "musicmp3/%(title)s.%(ext)s",
            'restrictfilenames': True,
            'nocheckcertificate': True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "2"
                }
            ],
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)
        self.guild_queues = {}
        self.guild_music_text_channels = {}
        self.guild_statuses = {}
        self.guild_current_users = {}
        self.voice_clients: Dict[int, GuildVoiceClient] = {}
        self.download_song_cooldowns = {}
        self.playlist_cooldowns = {}
        self.cooldowns = {}

    async def do_cooldown(self, user_id: int) -> None:
        self.cooldowns[user_id] = 1
        await asyncio.sleep(60)
        self.cooldowns[user_id] = 0
    
    async def do_playlist_cooldown(self, user_id: int) -> None:
        self.playlist_cooldowns[user_id] = 1
        await asyncio.sleep(60 * 60)
        self.playlist_cooldowns[user_id] = 0

    def generate_fingerprint(self, audio_file_path):
        try:
            result = subprocess.run(['fpcalc', audio_file_path], capture_output=True, text=True)
            fingerprint = result.stdout.strip().split('FINGERPRINT=')[1]
            duration = result.stdout.strip().split('TION=')[1].split("FINGERPRINT=")[0]
            return (fingerprint, duration)
        except Exception as e:
            #traceback.print_exception(e)
            return None
        
    def search_metadata_by_fingerprint(self, path, items):
        fingerprint, duration = items
        acoustid_api_key = ""
        acoustid_url = f'http://api.acoustid.org/v2/lookup?client={acoustid_api_key}&meta=recordings+releasegroups+compress&fingerprint={fingerprint}&duration={duration}'

        try:
            response = requests.get(acoustid_url)
            data = response.json()
            #print(response.text)
            if 'results' in data and data['results']:
                result = data['results'][0]
                recording = result['recordings'][0]
                title = recording.get('title', path)
                artists = recording.get('artists', [{'name': 'Unknown Artist'}])
                artist = artists['name']
                release_group = recording["releasegroups"][0]

                # Extracting additional metadata
                album = release_group.get('title', '')
                genre = release_group.get('genres', [])[0] if release_group.get('genres') else ''
                track_number = release_group.get('tracknum', 0)
                track_count = release_group.get('tracktotal', 0)
                disc_number = release_group.get('disnum', 0)
                disc_count = release_group.get('distotal', 0)
                album_artist = release_group.get('artist', '')
                year = release_group.get('year', 0)

                return {
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'genre': genre,
                    'track_number': track_number,
                    'track_count': track_count,
                    'disc_number': disc_number,
                    'disc_count': disc_count,
                    'album_artist': album_artist,
                    'year': year
                }
            else:
                print("No metadata found.")
                return None
        except Exception as e:
            #traceback.print_exception(e)
            return None

    def write_metadata_to_file(self, file_path, metadata):
        audiofile = eyed3.load(file_path)
        
        """audiofile.tag.title = metadata['title']
        audiofile.tag.artist = metadata['artist']
        audiofile.tag.album = metadata['album']
        audiofile.tag.genre = metadata['genre']
        audiofile.tag.track_num = metadata['track_number']
        audiofile.tag.track_total = metadata['track_count']
        audiofile.tag.disc_num = metadata['disc_number']
        audiofile.tag.disc_total = metadata['disc_count']
        audiofile.tag.album_artist = metadata['album_artist']
        audiofile.tag.release_date = str(metadata['year'])"""
        """tag.title = metadata['title']
        tag.artist = metadata['artist']
        tag.album = metadata['album']
        #tag.genre = metadata['genre']
        tag.track_num = metadata['track_number']
        #tag.track_total = metadata['track_count']
        #tag.disc_num = metadata['disc_number']
        #tag.disc_total = metadata['disc_count']
        tag.album_artist = metadata['album_artist']"""
        #tag.release_date = str(metadata['year'])
        audiofile.tag = eyed3.core.Tag(
            title = metadata['title'],
            artist = metadata['artist'],
            album = metadata['album'],
            album_artist = metadata['album_artist'],
            track_num = metadata['track_number']
        )
        audiofile.tag.save()

    def write_metadata_to_file(self, file_path: str, metadata: Dict[str, str] = {"none", "none"}):
        audiofile = ID3(file_path)

        audiofile.add(TIT2(encoding=3, text=metadata.get('title', file_path)))
        audiofile.add(TPE1(encoding=3, text=metadata.get('artist', "Unknown Artist")))
        audiofile.add(TALB(encoding=3, text=metadata.get('album', "Unknown Album")))
        audiofile.add(TCON(encoding=3, text=metadata.get('genre', "Unknown Genre")))
        audiofile.add(TRCK(encoding=3, text=str(metadata.get('track_number', 0))))
        audiofile.add(TPOS(encoding=3, text=str(metadata.get('disc_number', 0))))
        audiofile.add(TPE2(encoding=3, text=metadata.get('album_artist', "Unknown Album Artist")))
        audiofile.add(TDRC(encoding=3, text=str(metadata.get('year', 2024))))

        audiofile.save()

    async def fix_metadata(self, filepath: str):
        try:
            filepath = filepath.replace(".webm", ".mp3")
            fingerprint = self.generate_fingerprint(filepath)
            metadata = self.search_metadata_by_fingerprint(filepath, fingerprint)
            self.write_metadata_to_file(filepath, metadata)
        except Exception as e:
            #traceback.print_exception(e)
            pass

    async def play_music(self, guild: discord.Guild):
        client = self.voice_clients[guild.id]
        queue = client.queue
        channel = client.text_channel
        async with channel.typing():
            if len(queue) > 0:
                next_song_object = client.queue.pop(0)
                next_song = next_song_object.query
                user = next_song_object.user
                #self.guild_current_users[guild.id] = user
                if next_song_object.download:
                    filename = await downloader(next_song)
                    if "musicmp3" in filename:
                        pass
                    else:
                        filename = "musicmp3/" + filename
                    #await self.fix_metadata(filename)
                else:
                    if "musicmp3" in next_song:
                        filename = next_song
                    else:
                        filename = "musicmp3/" + next_song
                filename_0 = filename.replace("musicmp3/", "")
                filename_0 = filename_0.replace("musicmp3\\", "")
                filename_1 = filename.replace("_", "\_")
                guild.voice_client.play(discord.FFmpegPCMAudio(executable = "ffmpeg.exe", source = filename.replace(".webm", ".mp3")), after = lambda e: self.bot.loop.create_task(self.play_music(guild)))
                await channel.send(f'**Now Playing:** https://cocfire.xyz/musicplayer?fp={filename_0.replace(".webm", ".mp3")}\nReqested by: <@{user.id}>')
            else:
                self.guild_statuses[guild.id] = False
                self.guild_current_users[guild.id] = None
                await channel.send("The music queue has ended.")

    async def download_playlist(self, playlist_url: str):
        await wait()
        try:
            songs = []
            playlist_info = await self.get_playlist_info(playlist_url)
            for video_info in playlist_info:
                songs.append(await downloader(video_info['url']))
        except Exception as e:
            print(f'An error occurred while downloading playlist: {e}')

    async def get_playlist_info(self, playlist_url: str):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(playlist_url, download=False))
        playlist_info = []

        if 'entries' in data:
            for entry in data['entries']:
                video_info = {
                    'url': entry['url'],
                    'title': entry.get('title', 'Unknown Title'),
                }
                playlist_info.append(video_info)

        return playlist_info

    async def _downloader(self, query: str):
        quer1 = query.replace(':', '')
        quer2 = quer1.replace('/', '')
        await wait()
        try:
            filename = await YTDLSource.to_file(query, ytdl=self.ytdl, loop=self.bot.loop)
            apply_metadata("musicmp3/" + filename if not "musicmp3" in filename else filename)
        except Exception as e1:
            print(f'An error occured: {e1} (code e1)')
        filename=filename.replace(".webm", ".mp3")
        filename2=filename.replace('musicmp3\\', '')
        await wait()
        if not os.path.exists("musicmp3/" + filename2.replace(".mp3", ".mp4")):
            audio_clip=AudioFileClip("musicmp3/"+filename2)
            video_clip=VideoClip(lambda t: ImageClip('square.png').set_duration(audio_clip.duration).make_frame(t),duration=audio_clip.duration).set_audio(audio_clip)
            video_clip.write_videofile(filename=f"musicmp3/{filename2.replace('.mp3','.mp4')}",fps=1,codec='libx264',audio_codec='libmp3lame',threads=24,logger=None,ffmpeg_params=['-movflags', '+faststart'])
        return filename2

    @commands.hybrid_command(name="download_playlist", description="EXPERIMENTAL: downloads a YouTube playlist")
    async def download_playlist(self, ctx: commands.Context, *, playlist_url: str = None):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        return
        allowed_users = [self.bot.owner().id, 1069609771247882282]
        if ctx.author.id in cooldowns:
            if cooldowns[ctx.author.id] == 1:
                if ctx.author.id not in allowed_users:
                    return await command_on_cooldown(ctx)

        try:
            async with ctx.typing():
                existing_playlists = get_playlists(ctx.author.id)
                playlist_number = len(existing_playlists)
                if playlist_number > 24:
                    embed = discord.Embed(
                        title="Too Many Playlists",
                        description="You currently have too many playlists. Please delete one to continue.",
                        color=discord.Color.yellow()
                    )
                    return await ctx.send(embed=embed)

                loop = asyncio.get_event_loop()
                init_msg = await ctx.send("Extracting info...")
                asyncio.get_event_loop().create_task(self.do_playlist_cooldown(ctx.author.id))
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(playlist_url, download=False))
                playlist_info = []

                if 'entries' in data:
                    playlist_title = data.get('title', f'My Playlist {playlist_number}')
                    for entry in data['entries']:
                        video_info = {
                            'url': entry['url'],
                            'title': entry.get('title', 'Unknown Title'),
                        }
                        playlist_info.append(video_info)

                if not playlist_info:
                    return await ctx.send("No valid videos found in the playlist.")

                playlist_name = playlist_title
                playlist_path = f"users/user_{ctx.author.id}/playlists/{playlist_number}.lpl"

                current_track = 1
                await init_msg.edit(content=f"Beginning download of {len(playlist_info)} tracks... (please note that this may take a while)")

            with open(playlist_path, "w", encoding="utf-8") as playlist_file:
                playlist_file.write(playlist_name + "\n")
                for video_info in playlist_info:
                    init_msg = await ctx.send(content=f"({current_track}/{len(playlist_info)}) Downloading track \"{video_info['title']}\" now... (please note that this may take a while)", reference = get_message_reference(init_msg))
                    song_filename = await downloader(video_info['url'])
                    playlist_file.write(song_filename + "\n")
                    current_track += 1
                    await asyncio.sleep(3)

            embed = discord.Embed(
                title="Playlists",
                description=f"New playlist with name `{playlist_name}` was created and songs were added. You can access it using the playlist ID {playlist_number}.",
                color=discord.Color.yellow()
            )

            await init_msg.edit(content=f"You can access the playlist here: https://cocfire.xyz/musicplayer?user={ctx.author.id}&pl={playlist_number}", embed=embed)
            asyncio.get_event_loop().create_task(self.do_cooldown(ctx.author.id))
        except Exception as e:
            print(f'An error occurred while downloading playlist: {e}')
            await init_msg.edit(content="An error occurred during the playlist download.")


    @commands.hybrid_command(name="download_song", description="downloads a song from youtube. you can either provide a search term or a direct link to download", aliases=["download", "downloadsong"])
    async def download_song(self, ctx: commands.Context, *, query: str = None):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        async with ctx.typing():
            if ctx.guild.id == 1114828990373437520 or ctx.guild.id == 1077997767328288818:
                if ctx.channel.id != 1168237294688411648 and ctx.channel.id != 1190053765873676298:
                    if not ctx.author.id == self.bot.owner().id:
                        if not ctx.author.guild_permissions.administrator:
                            embed = discord.Embed(title="Wrong Channel",description="Go to <#1168237294688411648>/<#1190053765873676298> to use this command in this guild.",color=discord.Color.red())
                            return await ctx.send(embed=embed)

            allowed_users = [self.bot.owner().id, 1069609771247882282]
            if ctx.author.id in cooldowns:
                if cooldowns[ctx.author.id] == 1:
                    if ctx.author.id not in allowed_users:
                        return await command_on_cooldown(ctx)
            if query is None:
                return await ctx.send(f'Please provide a valid search term (Missing required argument "query")',reference=get_message_reference(ctx))
            await wait()
            try:
                embed = discord.Embed(
                    title="Song Downloader",
                    description=f"We're downloading the song `{query}` now. This may take a few seconds...",
                    color=discord.Color.blurple()
                )
                init_message = await ctx.send(embed=embed, reference=get_message_reference(ctx))
                await wait()
                filename = await downloader(query)
                await wait()
                await ctx.send(content=f"Here's your song!\nhttps://cocfire.xyz/musicplayer?fp={filename}\nBtw, you can now download songs through the website! Go to https://cocfire.xyz/musicplayer?action=download to test it out!",reference=get_message_reference(ctx))
                await init_message.delete()
                asyncio.get_event_loop().create_task(do_cooldown(ctx.author.id))
            except Exception as e1:
                print(f'An error occured: {e1} (code e1)')

    @commands.hybrid_command(name="playlists_help", description="shows the yt tutorial video for playlists")
    async def playlists_help(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        await ctx.reply("https://youtu.be/Gvb6P5yZ9tc")

    @commands.hybrid_command(name="show_playlists", description="shows all your playlists")
    async def show_playlists(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        playlists = get_playlists(ctx.author.id)
        embed = discord.Embed(
            title="Playlists",
            description="",
            color=discord.Color.yellow()
        )
        fields = 0
        excess = 0
        for playlist in playlists:
            with open(f"users/user_{ctx.author.id}/playlists/{playlist}", "r", encoding = "utf-8") as file:
                contents = [line.strip() if not line.strip() == "" else None for line in file.readlines()]
                name = contents.pop()
            if fields < 25:
                embed.add_field(name=name,value="\n".join(contents),inline=False)
                fields += 1
            else:
                excess += 1
        embed.set_footer(text = f"Plus `{excess}` others...")
        await ctx.send(embed=embed, reference = get_message_reference(ctx))

    @commands.hybrid_command(name="show_playlist", description="shows a playlist with a given id")
    async def show_playlist(self, ctx: commands.Context, plid: int):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        name, tracks = get_playlist(ctx.author.id, plid)
        embed = discord.Embed(
            title = f"Playlist: '{name}`",
            description = "Tracks:\n\n" + "\n".join(tracks),
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed, reference = get_message_reference(ctx))
        await ctx.send(f"You can access the playlist here: https://cocfire.xyz/musicplayer?user={ctx.author.id}&pl={plid}")
    
    @commands.hybrid_command(name = "play_playlist", description = "plays a playlist in the voice channel")
    async def play_playlist(self, ctx: commands.Context, plid: int):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        async with ctx.typing():
            try:
                name, tracks = get_playlist(ctx.author.id, plid)
                if len(tracks) == 0:
                    embed = discord.Embed(
                        title = "Playlist empty or not found",
                        description = "The playlist you have specified is either empty or nonexistant",
                        color=discord.Color.red()
                    )
                    return await ctx.send(embed=embed)
                embed = discord.Embed(
                    title = f"Playing from playlist '{name}'",
                    description = "Tracks:\n\n" + "\n".join(tracks),
                    color=discord.Color.yellow()
                )
                if ctx.guild.id not in self.voice_clients:
                    self.voice_clients[ctx.guild.id] = GuildVoiceClient()

                client = self.voice_clients[ctx.guild.id]

                for track in tracks:
                    queue_object = SongQueueObject(query = track.strip(), user = ctx.author, download = False)
                    client.queue.append(queue_object)

                if not ctx.author.voice:
                    return await ctx.send("You must be connected to a voice channel to use this command")
                if not ctx.guild.voice_client:
                    await ctx.author.voice.channel.connect()
                client.text_channel = ctx.channel
                if not client.is_playing:
                    client.is_playing = True
                    self.bot.loop.create_task(self.play_music(ctx.guild))

                await ctx.send(embed=embed)
                await ctx.send(f"You can access the playlist here: https://cocfire.xyz/musicplayer?user={ctx.author.id}&pl={plid}")
            except Exception as e:
                await ctx.send(f"Error: {traceback.format_exception(e)}")

    @commands.hybrid_command(name="create_new_playlist", description="creates a new playlist")
    async def create_new_playlist(self, ctx: commands.Context, *, playlist_name: str = None):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        existing_playlists = get_playlists(ctx.author.id)
        playlist_number = len(existing_playlists)
        if playlist_number > 24:
            embed = discord.Embed(
                title = "Too Many Playlists",
                description = "You currently have too many playlists. Please delete one to continue.",
                color=discord.Color.yellow()
            )
            return await ctx.send(embed=embed, reference = get_message_reference(ctx))
        
        if playlist_name is None:
            playlist_name = f"My Playlist {playlist_number}"

        with open(f"users/user_{ctx.author.id}/playlists/{playlist_number}.lpl", "w", encoding = "utf-8") as playlist_file:
            playlist_file.write(playlist_name + "\n")
        
        embed = discord.Embed(
            title = "Playlists",
            description = f"New playlist with name `{playlist_name}` was created. You can access it using the playlist ID {playlist_number}.",
            color=discord.Color.yellow()
        )

        await ctx.send(embed=embed, reference = get_message_reference(ctx))
        await ctx.send(f"You can access the playlist here: https://cocfire.xyz/musicplayer?user={ctx.author.id}&pl={playlist_number}")

    @commands.hybrid_command(name = "add_song_to_playlist", description = "adds a song to a playlist")
    async def add_song_to_playlist(self, ctx: commands.Context, playlist_id: int, *, query: str = None):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        async with ctx.typing():
            allowed_users = [self.bot.owner().id, 1069609771247882282]
            if ctx.author.id in cooldowns:
                if cooldowns[ctx.author.id] == 1:
                    if ctx.author.id not in allowed_users:
                        return await command_on_cooldown(ctx)
            name, tracks = get_playlist(ctx.author.id, playlist_id)
            if name == "NOT FOUND":
                embed = discord.Embed(
                    title = "Playlist not found",
                    description = "The playlist you have specified is nonexistant. Create a new playlist with `$create_new_playlist` or specify a valid playlist id.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed, reference=get_message_reference(ctx))
            if query is None:
                return await ctx.send(f'Please provide a valid search term (Missing required argument "query")', reference=get_message_reference(ctx))
            try:
                embed = discord.Embed(
                    title = "Playlist Song Downloader",
                    description = f"We're downloading the song `{query}` to add it to your playlist now. This may take a few seconds...",
                    color=discord.Color.blurple()
                )
                init_message = await ctx.send(embed=embed, reference=get_message_reference(ctx))
                await wait()
                filename = await downloader(query)
                if filename not in tracks:
                    with open(f"users/user_{ctx.author.id}/playlists/{playlist_id}.lpl", "a", encoding = "utf-8") as playlist_file:
                        playlist_file.write(filename + "\n")
                    embed = discord.Embed(
                        title = "Playlist Song Downloader",
                        description = f"We've added the song `{filename}` to your playlist."
                    )
                else:
                    embed = discord.Embed(
                        title = "Playlist Song Downloader",
                        description = f"The song `{filename}` is already in your playlist."
                    )
                await ctx.send(embed=embed)
                await init_message.delete()
                asyncio.get_event_loop().create_task(do_cooldown(ctx.author.id))
            except Exception as e1:
                print(f'An error occured: {e1} (code e1)')
        pass

    @commands.hybrid_command(name = "fix_music", description = "resets the music bot for the guild")
    async def fix_music(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if not ctx.guild:
            return await command_not_used_in_guild(ctx)
        async with ctx.typing():
            if ctx.guild.voice_client:
                try:
                    await ctx.guild.voice_client.disconnect()
                    ctx.guild.voice_client.cleanup()
                except:
                    pass
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
            await ctx.send("Fixed voice client..")

    @commands.hybrid_command(name = "shuffle", description = "shuffles the queue")
    async def shuffle(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if not ctx.guild:
            return await command_not_used_in_guild(ctx)
        async with ctx.typing():
            if ctx.guild.id not in self.voice_clients:
                self.voice_clients[ctx.guild.id] = GuildVoiceClient()
            client = self.voice_clients[ctx.guild.id]
            if len(client.queue) > 1:
                random.shuffle(client.queue)
            await ctx.send("Shuffled queue")

    @commands.hybrid_command(name = "play", description = "plays a song in vc from youtube")
    async def play(self, ctx: commands.Context, *, url: str):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        try:
            if not ctx.author.voice:
                return await ctx.send("You must be connected to a voice channel to use this command")
            if not ctx.guild.voice_client:
                await ctx.author.voice.channel.connect()
            if ctx.guild.id not in self.voice_clients:
                self.voice_clients[ctx.guild.id] = GuildVoiceClient()
            client = self.voice_clients[ctx.guild.id]
            filename = await downloader(url)
            client.queue.append(SongQueueObject(filename, ctx.author, download=False))
            client.text_channel = ctx.channel
            if not client.is_playing:
                client.is_playing = True
                self.bot.loop.create_task(self.play_music(ctx.guild))
                return
            await ctx.send("The song has been added to the queue")
        except Exception as e:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.hybrid_command()
    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)

        if not ctx.guild:
            return await command_not_used_in_guild(ctx)
        if ctx.guild.id not in self.voice_clients:
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
        client = self.voice_clients[ctx.guild.id]
        if ctx.guild.voice_client:
            try:
                user = client.current_user
                if user is not None:
                    if ctx.author.id != user.id:
                        if not ctx.author.guild_permissions.moderate_members:
                            if not ctx.author.id == self.bot.owner().id:
                                return await insuf_perms(ctx, "moderate_members, song_requestor")
            except: pass
        skip_connected_check = False
        if channel:
            skip_connected_check = True
        if not ctx.message.author.voice:
            if not skip_connected_check:
                return await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
        else:
            channel = ctx.message.author.voice.channel

        permissions = channel.permissions_for(ctx.guild.me)
        if not permissions.connect or not permissions.speak:
            embed = discord.Embed(
                title = "Insufficient Permission(s)",
                description = "I don't have permission to join or speak in this voice channel.\nPlease go to the channel's settings > Permissions > Roles/Members > CoCFire's Pet, then select `View Channel`, `Connect`, and `Speak`.",
                color=discord.Color.red(),
                timestamp = datetime.datetime.now()
            )
            return await ctx.send(embed=embed, reference=get_message_reference(ctx))

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            ctx.guild.voice_client.cleanup()
        await channel.connect()

    @commands.hybrid_command(name = "pause", description = "pause the music")
    async def pause(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if not ctx.guild.voice_client:
            return await ctx.send("The bot isn't connect to a channel")
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.hybrid_command(name = "resume", description = "resume the music")
    async def resume(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if not ctx.guild.voice_client:
            return await ctx.send("The bot isn't connected to a channel")
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play command")

    @commands.hybrid_command(name = "leave", description = "makes the bot leave the current voice channel")
    async def leave(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if ctx.guild.id not in self.voice_clients:
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
        client = self.voice_clients[ctx.guild.id]
        try:
            user = client.current_user
            if user is not None:
                if ctx.author.id != user.id:
                    if not ctx.author.guild_permissions.moderate_members:
                        if not ctx.author.id == self.bot.owner().id:
                            return await insuf_perms(ctx, "moderate_members, song_requestor")
        except: pass

        if not ctx.guild.voice_client:
            return await ctx.send("The bot isn't connected to a channel")
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            voice_client.cleanup()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.hybrid_command(name = "stop", description = "stop the music currently playing")
    async def stop(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if ctx.guild.id not in self.voice_clients:
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
        client = self.voice_clients[ctx.guild.id]
        try:
            user = client.current_user
            if user is not None:
                if ctx.author.id != user.id:
                    if not ctx.author.guild_permissions.moderate_members:
                        if not ctx.author.id == self.bot.owner().id:
                            return await insuf_perms(ctx, "moderate_members, song_requestor")
        except: pass

        if not ctx.guild.voice_client:
            return await ctx.send("The bot isn't connected to a channel")
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            client.queue = []
            client.current_user = None
            client.is_playing = False
            voice_client.stop()
            await ctx.send("Stopped.")
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.hybrid_command(name = "skip", description = "skip the currently playing song")
    async def skip(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if ctx.guild.id not in self.voice_clients:
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
        client = self.voice_clients[ctx.guild.id]
        try:
            user = client.current_user
            if user is not None:
                if ctx.author.id != user.id:
                    if not ctx.author.guild_permissions.moderate_members:
                        if not ctx.author.id == self.bot.owner().id:
                            return await insuf_perms(ctx, "moderate_members, song_requestor")
        except:
            return await ctx.send("The bot isn't connected to a voice channel")

        if not ctx.author.voice:
            return await ctx.send("You must be connected to a voice channel to use this command")
        voice_client = ctx.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
        else:
            return await ctx.send("The bot is not playing anything at the moment")
        
    @commands.hybrid_command(name = "queue", description = "shows the song queue")
    async def show_queue(self, ctx: commands.Context):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)
        if ctx.guild.id not in self.voice_clients:
            self.voice_clients[ctx.guild.id] = GuildVoiceClient()
        client = self.voice_clients[ctx.guild.id]
        async with ctx.typing():
            queue = client.queue
            if len(queue) > 0:
                resp_string = ""
                numb = 0
                for item in queue:
                    filename = item.query
                    user = item.user
                    filename_1 = filename.replace("_", "\_")
                    numb += 1
                    resp_string = resp_string + f'**{numb}.** {filename_1.replace(".webm", ".mp3")} **Reqested by:** <@{user.id}>\n'
                embed = discord.Embed(
                    title = "Song Queue:",
                    description = resp_string,
                    color = discord.Color.green()
                )
                await ctx.send(embed = embed)
            else:
                await ctx.send("The queue is empty!")


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def to_file(self, url, *, ytdl, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)

        if os.path.exists(filename.replace(".webm", ".mp3")): return filename

        try: await loop.run_in_executor(None, lambda: ytdl.download([url]))
        except Exception as e: print(f"An error occurred during download: {e}")
        return filename

__all__ = [
    'MusicBotCog',
    'downloader',
    #'search_songs', 
    #'get_music', 
    #'get_playlist', 
    #'get_playlists'
]
