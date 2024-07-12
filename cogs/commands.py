import discord
from discord.ext import commands
from discord import app_commands

import time
import asyncio


class StatusView(discord.ui.View):
    def __init__(self, client, time_started):
        super().__init__(timeout=None)
        self.client = client
        self.time_started = time_started
        self.message = None

    @discord.ui.button(label="Stop Updating", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        button.disabled = True
        button.label = "Updates Stopped"
        await interaction.response.edit_message(view=self)

    async def update_embed(self):
        while not self.is_finished():
            now = time.time()
            uptime = now - self.time_started
            uptime_sec = int(uptime % 60)
            uptime_min = int((uptime // 60) % 60)
            uptime_hour = int((uptime // 3600) % 24)
            uptime_day = int(uptime // 86400)

            # Fetch current latency
            latency = round(self.client.latency * 1000)

            status_embed = discord.Embed(title="Status", description="How well is Duckmin running?",
                                         colour=discord.Colour.blue())
            status_embed.add_field(name="📶 Ping", value=f"Latency: {latency}ms", inline=False)
            status_embed.add_field(name="⌚ Uptime",
                                   value=f"{uptime_day:02d}:{uptime_hour:02d}:{uptime_min:02d}:{uptime_sec:02d}",
                                   inline=True)
            status_embed.set_footer(text="Last updated")
            status_embed.timestamp = discord.utils.utcnow()

            if self.message:
                await self.message.edit(embed=status_embed)

            await asyncio.sleep(5)


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.colour = 0xf4d45e
        self.time_started = time.time()

    # github (link, suggestions)
    @app_commands.command(name="repo", description="The link to the bots repo")
    async def repo(self, interaction: discord.Interaction):
        link = "https://github.com/BrownTurtleBear/ianland-bot"
        github_embed = discord.Embed(title="Link to Duckmin's repo", description="See how the bot works on the repo!\nAll suggestions are wellcome.", url=link, colour=self.colour)
        github_embed.set_thumbnail(url=self.client.user.avatar.url)
        await interaction.response.send_message(embed=github_embed)

    # Status (ping, uptime)
    @app_commands.command(name="status", description="How well is Duckmin running?")
    async def status(self, interaction: discord.Interaction):
        view = StatusView(self.client, self.time_started)
        await interaction.response.send_message("Loading status...", ephemeral=True)
        message = await interaction.original_response()
        view.message = message

        self.client.loop.create_task(view.update_embed())
        await message.edit(content=None, view=view)


async def setup(client):
    await client.add_cog(Commands(client))
    print("- commands.py loaded -")
