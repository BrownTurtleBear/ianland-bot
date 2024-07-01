import discord
from discord.ext import commands
from discord import app_commands

import time


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.colour = 0xf4d45e
        global time_started
        time_started = time.time()

    # github
    @app_commands.command(name="repo", description="The link to the bots repo")
    async def repo(self, interaction: discord.Interaction):
        link = "https://github.com/BrownTurtleBear/ianland-bot"
        github_embed = discord.Embed(title="Link to Duckmin's repo", description="See how the bot works on the repo!\nAll suggestions are wellcome.", url=link, colour=self.colour)
        github_embed.set_thumbnail(url=self.client.user.avatar.url)
        await interaction.response.send_message(embed=github_embed)

    @app_commands.command(name="status", description="How well is Duckmin running?")
    async def status(self, interaction: discord.Interaction):
        now = time.time()
        uptime = now - time_started
        uptime_sec = round(uptime)
        uptime_min = round(uptime / 60)
        uptime_hour = round(uptime / 3600)
        uptime_day = round(uptime / 86400)
        latency = round(self.client.latency * 1000)
        status_embed = discord.Embed(title="Status", description=f"How well is Duckmin running?", colour=self.colour)
        status_embed.add_field(name="📶 Ping 📶", value=f"Latency : {latency}ms.", inline=False)
        status_embed.add_field(name="⌚ Uptime ⌚", value=f"{uptime_day}:{uptime_hour}:{uptime_min}:{uptime_sec}", inline=True)
        await interaction.response.send_message(embed=status_embed)


async def setup(client):
    await client.add_cog(Commands(client))
