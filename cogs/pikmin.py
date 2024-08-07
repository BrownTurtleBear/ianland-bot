import discord
from discord.ext import commands
from discord import app_commands


class Pikmin(commands.Cog):
    def __init__(self, client):
        self.client = client

    color_map = {
        'red': '#FF0000',
        'blue': '#0000FF',
        'green': '#00FF00',
        'yellow': '#FFFF00',
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'black': '#000000',
        'white': '#FFFFFF',
        'gray': '#808080',
        'orange': '#FFA500',
        'purple': '#800080',
        'brown': '#A52A2A',
        'pink': '#FFC0CB',
        'lime': '#00FF00',
        'indigo': '#4B0082',
        'violet': '#EE82EE',
        'gold': '#FFD700',
        'silver': '#C0C0C0',
    }

    @app_commands.command(name="coloured_name",
                          description="Generate a coloured name for your Pikmin using Unity rich text format.")
    @app_commands.describe(
        name="The name for your Pikmin",
        color="Color name (e.g., red, blue, green) or hex code (e.g., #FF0000)",
        bold="Make the name bold",
        italic="Make the name italic"
    )
    async def coloured_name(
            self,
            interaction: discord.Interaction,
            name: str,
            color: str = None,
            bold: bool = False,
            italic: bool = False
    ):
        formatted_name = name

        if bold:
            formatted_name = f"<b>{formatted_name}</b>"

        if italic:
            formatted_name = f"<i>{formatted_name}</i>"

        if color:
            color = color.lower()
            if color in self.color_map:
                color = self.color_map[color]
            if color.startswith('#'):
                color = color[1:]
            formatted_name = f"<color=#{color}>{formatted_name}</color>"

        await interaction.response.send_message("Here's your formatted Pikmin name:")
        await interaction.followup.send(f"`{formatted_name}`")
        await interaction.followup.send(
            "If you want multiple colours, run the /coloured_name command again and add it to the end of the one you just generated.")


async def setup(client):
    await client.add_cog(Pikmin(client))
    print("- pikmin.py loaded -")
