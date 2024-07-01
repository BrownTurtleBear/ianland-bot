import discord
from discord.ext import commands
import asyncio
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN')


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="?", intents=discord.Intents().all())
        self.coglist = []
        self.logger = logging.getLogger("logger")
        self.logger.addHandler(logging.FileHandler("logger.log"))
        self.logger.setLevel(logging.DEBUG)

    async def on_ready(self):
        try:
            print(f"Successfully logged in as {self.user}!")
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands!")
            syn = await self.tree.sync(guild=discord.Object(id="ID Here"))
            print(f'Synced {len(syn)} in {syn[0].guild.name}' if syn else 'No commands were synced')
        except Exception as err:
            client.logger.error(err)
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="to help"))

    async def setup_hook(self):
        for ext in self.coglist:
            await self.load_extension(ext)


client = Client()

logging.basicConfig(filename="log.txt", level=logging.INFO)


async def main():
    try:
        await client.start(token)
    except Exception as err:
        client.logger.error(err)


if __name__ == "__main__":
    asyncio.run(main())
