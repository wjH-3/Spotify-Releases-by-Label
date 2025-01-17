import os
import discord
from discord.ext import commands, tasks
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime, timezone
import asyncio
from dotenv import load_dotenv

# Environment variables for API keys and tokens
load_dotenv('tokens.env')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# List of label IDs to track (you can add more)
LABELS_TO_TRACK = [
    "The Third Movement",
    "Heresy",
    "Broken Strain",
    "Spoontech Records",
    "Mirror Society"
]

# Initialize Spotify client
spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Store the last check timestamp
last_check = {}

async def check_new_releases():
    """Check for new releases from specified labels"""
    new_releases = []
    
    for label_id in LABELS_TO_TRACK:
        # Get all albums from the label
        results = spotify.search(
            f'label:"{label_id}" tag:new',
            type='album',
            limit=5,
        )
        
        for item in results['albums']['items']:
            # Check if the release is new (released today)
            release_date = datetime.strptime(item['release_date'], '%Y-%m-%d')
            release_date = release_date.replace(tzinfo=timezone.utc)
            
            # If this is a new release we haven't seen before
            if (label_id not in last_check or 
                release_date > last_check[label_id]):
                # Fetch detailed album information
                album_results = spotify.album(item['id'])
                
                # Check if the album's label matches any in LABELS_TO_TRACK
                if album_results['label'] in LABELS_TO_TRACK:
                    new_releases.append({
                        'name': album_results['name'],
                        'artists': [artist['name'] for artist in album_results['artists']],
                        'url': album_results['external_urls']['spotify'],
                        'label': album_results['label'],
                        'release_date': album_results['release_date'],
                        'image_url': album_results['images'][0]['url'] if album_results['images'] else None
                    })
        
        # Update last check time for this label
        last_check[label_id] = datetime.now(timezone.utc)
    
    return new_releases

async def create_release_embed(release):
    """Create a consistent embed for releases"""
    embed = discord.Embed(
        title=f"{release['name']}",
        url=release['url'],
        color=discord.Color.green()
    )
    
    if release['image_url']:
        embed.set_thumbnail(url=release['image_url'])
    
    # Add fields vertically (not inline)
    embed.add_field(
        name="Artist(s)",
        value=", ".join(release['artists']),
        inline=False
    )
    embed.add_field(
        name="Label",
        value=release['label'],
        inline=False
    )
    embed.add_field(
        name="Release Date",
        value=release['release_date'],
        inline=False
    )
    
    return embed

@tasks.loop(hours=24)
async def check_and_notify():
    """Check for new releases every 24 hours"""
    # Only run on Fridays at 12 PM GMT
    now = datetime.now(timezone.utc)
    
    if now.hour != 12:  # 12 PM UTC
        return
        
    new_releases = await check_new_releases()
    
    if new_releases:
        for guild in bot.guilds:
            # Find the first text channel we can send messages in
            channel = next((
                channel for channel in guild.text_channels 
                if channel.permissions_for(guild.me).send_messages
            ), None)
            if channel:       
                for release in new_releases:
                    embed = await create_release_embed(release)
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending to {guild.name}: {str(e)}")

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'{bot.user} has connected to Discord!')
    check_and_notify.start()

@bot.command(name='check')
async def check_all(ctx):
    """Manual command to check for new releases"""
    await ctx.send("Checking for new releases...")
    new_releases = await check_new_releases()
    
    if not new_releases:
        await ctx.send("No new releases found.")
        return
    
    for release in new_releases:
        embed = await create_release_embed(release)
        await ctx.send(embed=embed)

@bot.command(name='labels')
async def list_labels(ctx):
    """Command to list all labels being tracked"""
    embed = discord.Embed(
        title="Currently Tracked Labels",
        description="The following labels are being monitored for new releases:",
        color=discord.Color.blue()
    )
    
    # Add each label as a bullet point
    labels_list = "\n".join(f"• {label}" for label in LABELS_TO_TRACK)
    embed.add_field(
        name="Labels",
        value=labels_list,
        inline=False
    )
    
    await ctx.send(embed=embed)

def main():
    """Main function to run the bot"""
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
