import os
import discord
from discord.ext import commands, tasks
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime, timezone
import asyncio

# Environment variables for API keys and tokens
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# List of label IDs to track (you can add more)
LABELS_TO_TRACK = [
    "The Third Movement",
    "Heresy",
    "Broken Strain",
    "Spoontech Records"
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
bot = commands.Bot(command_prefix='/', intents=intents)

# Store the last check timestamp
last_check = {}

async def check_new_releases():
    """Check for new releases from specified labels"""
    new_releases = []
    
    for label_id in LABELS_TO_TRACK:
        # Get all albums from the label
        results = spotify.search(
            f"label:{label_id}",
            type='album',
            limit=3,
            market='US'
        )
        
        for item in results['albums']['items']:
            # Check if the release is new (released today)
            release_date = datetime.strptime(item['release_date'], '%Y-%m-%d')
            release_date = release_date.replace(tzinfo=timezone.utc)
            
            # If this is a new release we haven't seen before
            if (label_id not in last_check or 
                release_date > last_check[label_id]):
                new_releases.append({
                    'name': item['name'],
                    'artists': [artist['name'] for artist in item['artists']],
                    'url': item['external_urls']['spotify'],
                    'label': label_id
                })
        
        # Update last check time for this label
        last_check[label_id] = datetime.now(timezone.utc)
    
    return new_releases

@tasks.loop(hours=24)
async def check_and_notify():
    """Check for new releases every 24 hours"""
    # Only run on Fridays at 12 PM GMT
    now = datetime.now(timezone.utc)
    if now.weekday() != 4:  # 4 is Friday
        return
    
    if now.hour != 12:  # 12 PM GMT
        return
    
    new_releases = await check_new_releases()
    
    if new_releases:
        channel = bot.get_channel(CHANNEL_ID)
        
        for release in new_releases:
            # Create and send embedded message
            embed = discord.Embed(
                title="New Release! 🎵",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Album",
                value=release['name'],
                inline=False
            )
            embed.add_field(
                name="Artists",
                value=", ".join(release['artists']),
                inline=False
            )
            embed.add_field(
                name="Listen on Spotify",
                value=release['url'],
                inline=False
            )
            
            await channel.send(embed=embed)

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
        embed = discord.Embed(
            title="New Release! 🎵",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Album",
            value=release['name'],
            inline=False
        )
        embed.add_field(
            name="Artists",
            value=", ".join(release['artists']),
            inline=False
        )
        embed.add_field(
            name="Listen on Spotify",
            value=release['url'],
            inline=False
        )
        
        await ctx.send(embed=embed)

def main():
    """Main function to run the bot"""
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
