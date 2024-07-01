import discord
from discord.ext import commands
from discord import app_commands


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="share")
    async def share(self, interaction:discord.Interaction):
        a
async def setup(client):
    await client.add_cog(Music(client))
