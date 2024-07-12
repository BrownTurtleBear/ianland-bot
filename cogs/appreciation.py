import discord
from discord.ext import commands
from discord import app_commands
import json
import datetime
import pytz
import random


class Appreciation(commands.Cog):
    def __init__(self, client):
        self.saved_appreciations = None
        self.appreciations = None
        self.client = client
        self.appreciations_file = "appreciations.json"
        self.saved_appreciations_file = "saved_appreciations.json"
        self.load_appreciations()
        self.load_saved_appreciations()

    def load_appreciations(self):
        try:
            with open(self.appreciations_file, "r") as f:
                self.appreciations = json.load(f)
        except FileNotFoundError:
            self.appreciations = {}

    def save_appreciations(self):
        with open(self.appreciations_file, "w") as f:
            json.dump(self.appreciations, f)

    def load_saved_appreciations(self):
        try:
            with open(self.saved_appreciations_file, "r") as f:
                self.saved_appreciations = json.load(f)
        except FileNotFoundError:
            self.saved_appreciations = {}

    def save_saved_appreciations(self):
        with open(self.saved_appreciations_file, "w") as f:
            json.dump(self.saved_appreciations, f)

    @staticmethod
    def get_adelaide_date():
        adelaide_tz = pytz.timezone("Australia/Adelaide")
        return datetime.datetime.now(adelaide_tz).date().isoformat()

    def clean_old_appreciations(self):
        today = self.get_adelaide_date()
        for guild_id in self.appreciations:
            self.appreciations[guild_id] = {k: v for k, v in self.appreciations[guild_id].items() if v["date"] == today}
        self.save_appreciations()

    @app_commands.command(name="appreciate", description="Your daily appreciation.")
    async def appreciate(self, interaction: discord.Interaction):
        self.clean_old_appreciations()
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        today = self.get_adelaide_date()

        if guild_id not in self.appreciations:
            self.appreciations[guild_id] = {}

        if user_id in self.appreciations[guild_id] and self.appreciations[guild_id][user_id]["date"] == today:
            view = AppreciationOptionsView(self, guild_id, user_id)
            await interaction.response.send_message(
                "You've already shared an appreciation today. What would you like to do?", view=view, ephemeral=True)
        else:
            await interaction.response.send_modal(AppreciationModal(self, guild_id, user_id))

    @app_commands.command(name="show_appreciations",
                          description="Look through the appreciations that someone had today.")
    async def show_appreciations(self, interaction: discord.Interaction):
        self.clean_old_appreciations()
        guild_id = str(interaction.guild_id)
        today = self.get_adelaide_date()

        if guild_id not in self.appreciations:
            await interaction.response.send_message(
                "No appreciations have been shared today. I would love to know what you find appreciative today.",
                ephemeral=True)
            return

        today_appreciations = [v["appreciation"] for v in self.appreciations[guild_id].values() if v["date"] == today]

        if not today_appreciations:
            await interaction.response.send_message("No appreciations have been shared in this server today.",
                                                    ephemeral=True)
            return

        appreciation = random.choice(today_appreciations)
        embed = discord.Embed(title="A Appreciation", description=appreciation,
                              color=discord.Color.green())

        view = AppreciationView(self, interaction.guild_id, interaction.user.id, today_appreciations, appreciation)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="saved_appreciations", description="See your saved appreciations.")
    async def saved_appreciations(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        if guild_id not in self.saved_appreciations or user_id not in self.saved_appreciations[guild_id] or not \
                self.saved_appreciations[guild_id][user_id]:
            view = ShowAppreciationsView(self, interaction.guild_id, interaction.user.id)
            await interaction.response.send_message(
                "You haven't saved any appreciations yet. Would you like to see today's appreciations?",
                view=view, ephemeral=True)
            return

        saved_list = self.saved_appreciations[guild_id][user_id]
        view = SavedAppreciationView(self, guild_id, user_id, saved_list)
        embed = discord.Embed(title=f"Saved Appreciation 1/{len(saved_list)}", description=saved_list[0],
                              color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        saved_list = self.saved_appreciations[guild_id][user_id]
        view = SavedAppreciationView(self, guild_id, user_id, saved_list)
        embed = discord.Embed(title=f"Saved Appreciation 1/{len(saved_list)}", description=saved_list[0],
                              color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class AppreciationModal(discord.ui.Modal, title="Daily Appreciation"):
    appreciation = discord.ui.TextInput(
        label="What do you appreciate today?",
        style=discord.TextStyle.paragraph,
        placeholder="Express till your heart's content!"
    )

    def __init__(self, appreciation_cog, guild_id, user_id, initial_value=""):
        super().__init__()
        self.appreciation_cog = appreciation_cog
        self.guild_id = guild_id
        self.user_id = user_id
        if initial_value:
            self.appreciation.default = initial_value

    async def on_submit(self, interaction: discord.Interaction):
        today = Appreciation.get_adelaide_date()

        if self.guild_id not in self.appreciation_cog.appreciations:
            self.appreciation_cog.appreciations[self.guild_id] = {}

        self.appreciation_cog.appreciations[self.guild_id][self.user_id] = {
            "date": today,
            "appreciation": self.appreciation.value
        }
        self.appreciation_cog.save_appreciations()

        await interaction.response.send_message(
            f"Thanks for sharing your appreciation for today. Have a nice rest of your day and see you tomorrow.",
            ephemeral=True)


class AppreciationOptionsView(discord.ui.View):
    def __init__(self, appreciation_cog, guild_id, user_id):
        super().__init__()
        self.appreciation_cog = appreciation_cog
        self.guild_id = guild_id
        self.user_id = user_id

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_appreciation = self.appreciation_cog.appreciations[self.guild_id][self.user_id]["appreciation"]
        await interaction.response.send_modal(
            AppreciationModal(self.appreciation_cog, self.guild_id, self.user_id, current_appreciation))

    @discord.ui.button(label="Come back tomorrow", style=discord.ButtonStyle.secondary)
    async def come_back_tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("See you tomorrow. Have a nice day!", ephemeral=True)


class AppreciationView(discord.ui.View):
    def __init__(self, appreciation_cog, guild_id, user_id, appreciations, current_appreciation):
        super().__init__()
        self.appreciation_cog = appreciation_cog
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self.appreciations = appreciations
        self.current_appreciation = current_appreciation
        self.shown_appreciations = {current_appreciation}

    @discord.ui.button(label="Save", style=discord.ButtonStyle.green)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in self.appreciation_cog.saved_appreciations:
            self.appreciation_cog.saved_appreciations[self.guild_id] = {}
        if self.user_id not in self.appreciation_cog.saved_appreciations[self.guild_id]:
            self.appreciation_cog.saved_appreciations[self.guild_id][self.user_id] = []
        if self.current_appreciation not in self.appreciation_cog.saved_appreciations[self.guild_id][self.user_id]:
            self.appreciation_cog.saved_appreciations[self.guild_id][self.user_id].append(self.current_appreciation)
            self.appreciation_cog.save_saved_appreciations()
            await interaction.response.send_message("Appreciation saved!", ephemeral=True)
        else:
            await interaction.response.send_message("You've already saved this appreciation.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        remaining_appreciations = [a for a in self.appreciations if a not in self.shown_appreciations]

        if not remaining_appreciations:
            # If all appreciations have been shown, start over
            self.shown_appreciations.clear()
            remaining_appreciations = self.appreciations

        self.current_appreciation = random.choice(remaining_appreciations)
        self.shown_appreciations.add(self.current_appreciation)

        embed = discord.Embed(title="A Appreciation", description=self.current_appreciation,
                              color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=self)


class SavedAppreciationView(discord.ui.View):
    def __init__(self, appreciation_cog, guild_id, user_id, saved_list):
        super().__init__()
        self.appreciation_cog = appreciation_cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.saved_list = saved_list
        self.current_index = 0
        self.confirming_forget = False

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = (self.current_index - 1) % len(self.saved_list)
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = (self.current_index + 1) % len(self.saved_list)
        await self.update_message(interaction)

    @discord.ui.button(label="Forget", style=discord.ButtonStyle.red)
    async def forget(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.confirming_forget:
            self.confirming_forget = True
            await interaction.response.send_message(
                "Are you sure you want to forget this appreciation? Click the Forget button again to confirm.",
                ephemeral=True)
        else:
            removed_appreciation = self.saved_list.pop(self.current_index)
            self.appreciation_cog.saved_appreciations[self.guild_id][self.user_id] = self.saved_list
            self.appreciation_cog.save_saved_appreciations()

            if not self.saved_list:
                await interaction.response.edit_message(content="You have no more saved appreciations.", embed=None,
                                                        view=None)
            else:
                self.current_index = min(self.current_index, len(self.saved_list) - 1)
                await self.update_message(interaction)

            self.confirming_forget = False

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Saved Appreciation {self.current_index + 1}/{len(self.saved_list)}",
            description=self.saved_list[self.current_index],
            color=discord.Color.blue()
        )
        self.confirming_forget = False  # Reset confirmation state when changing appreciation
        await interaction.response.edit_message(embed=embed, view=self)


class ShowAppreciationsView(discord.ui.View):
    def __init__(self, appreciation_cog, guild_id, user_id):
        super().__init__()
        self.appreciation_cog = appreciation_cog
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)

    @discord.ui.button(label="Show Today's Appreciations", style=discord.ButtonStyle.primary)
    async def show_appreciations(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.appreciation_cog.clean_old_appreciations()
        today = self.appreciation_cog.get_adelaide_date()

        if self.guild_id not in self.appreciation_cog.appreciations:
            await interaction.response.send_message(
                "No appreciations have been shared today. I would love to know what you find appreciative today.",
                ephemeral=True)
            return

        today_appreciations = [v["appreciation"] for v in self.appreciation_cog.appreciations[self.guild_id].values() if
                               v["date"] == today]

        if not today_appreciations:
            await interaction.response.send_message("No appreciations have been shared in this server today.",
                                                    ephemeral=True)
            return

        appreciation = random.choice(today_appreciations)
        embed = discord.Embed(title="A Appreciation", description=appreciation,
                              color=discord.Color.green())

        view = AppreciationView(self.appreciation_cog, self.guild_id, self.user_id, today_appreciations, appreciation)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(client):
    await client.add_cog(Appreciation(client))
    print("- appreciation.py loaded -")
