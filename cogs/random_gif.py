import discord
from discord import app_commands
from discord.ext import commands
import random


class GifCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = bot.tenor_api_key
        self.ckey = "duckmin"
        if not self.api_key:
            raise ValueError("TENOR_API_KEY not found")

    async def get_random_gif(self, search_term):
        limit = 50

        # Construct the API URL
        url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={self.api_key}&client_key={self.ckey}&limit={limit}"

        # Make the API request
        async with self.bot.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])

                if results:
                    # Select a random GIF from the results
                    random_gif = random.choice(results)
                    return random_gif['media_formats']['gif']['url']
                else:
                    return "No GIFs found for the given search term."
            else:
                error_text = await response.text()
                print(f"Error {response.status}: {error_text}")
                return f"Error: {response.status}"

    @app_commands.command(name='randomgif')
    @app_commands.choices(choice=[
        app_commands.Choice(name='Splatoon', value='splatoon'),
        app_commands.Choice(name='Pikmin', value='pikmin')
    ])
    async def random_gif(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        gif_url = await self.get_random_gif(choice.value)
        await interaction.response.send_message(f"Random {choice.name} GIF: {gif_url}")


async def setup(bot):
    await bot.add_cog(GifCog(bot))
