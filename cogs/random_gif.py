import discord
from discord import app_commands
from discord.ext import commands
import random
import time


class GifCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = bot.tenor_api_key
        self.ckey = "my_test_app"
        if not self.api_key:
            raise ValueError("TENOR_API_KEY not found in environment variables")

    async def get_related_terms(self, search_term):
        url = f"https://tenor.googleapis.com/v2/search_suggestions?q={search_term}&key={self.api_key}&client_key={self.ckey}"

        async with self.bot.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('results', [])
            else:
                print(f"Error fetching related terms: {response.status}")
                return []

    async def get_random_gif(self, initial_search_term):
        related_terms = await self.get_related_terms(initial_search_term)
        all_terms = [initial_search_term] + related_terms
        search_term = random.choice(all_terms)

        limit = 50  # Increased to get more variety
        max_count = 1000
        random_start = random.randint(0, max_count - limit)

        # Add a random query parameter to prevent caching
        random_param = f"nocache={int(time.time())}"

        url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={self.api_key}&client_key={self.ckey}&limit={limit}&pos={random_start}&{random_param}"

        async with self.bot.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])

                if results:
                    # Choose a random GIF from the results
                    random_gif = random.choice(results)
                    return random_gif['media_formats']['gif']['url']
                else:
                    return None
            else:
                print(f"Error {response.status}: {await response.text()}")
                return None

    @app_commands.command(name='randomgif', description="Generate a random splatoon or pikmin gif")
    @app_commands.choices(choice=[
        app_commands.Choice(name='Splatoon', value='splatoon'),
        app_commands.Choice(name='Pikmin', value='pikmin')
    ])
    async def random_gif(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        gif_url = await self.get_random_gif(choice.value)
        if gif_url:
            await interaction.response.send_message(gif_url)
        else:
            await interaction.response.send_message("Sorry, couldn't find a GIF.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GifCog(bot))
    print("- random_gif.py loaded -")