import discord
from discord.ext import commands
from discord import app_commands


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client

    # github
    @app_commands.command(name="github", description="The link to the bots repo")
    async def github(self, interaction=discord.Interaction):
        link = "https://github.com/BrownTurtleBear/ianland-bot"
        github_embed = discord.Embed(title="Link to bots repo", url=link)
        github_embed.set_thumbnail(url=self.client.user.avatar.url)
        await interaction.response.send_message(embed=github_embed)

async def setup(client):
    await client.add_cog(Commands(client))
