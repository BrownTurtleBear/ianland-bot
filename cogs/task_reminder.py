import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import json


class TaskReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.load_tasks()

    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as f:
                self.tasks = json.load(f)
        except FileNotFoundError:
            self.tasks = {}

    def save_tasks(self):
        with open('tasks.json', 'w') as f:
            json.dump(self.tasks, f)

    @app_commands.command(name="add_task", description="Add a new task with a due date")
    @app_commands.describe(
        task="The task you need to complete (e.g., 'Finish project report')",
        due_date="The date the task is due, in MM-DD format (e.g., '07-15' for July 15)"
    )
    async def add_task(self, interaction: discord.Interaction, task: str, due_date: str):
        try:
            month, day = map(int, due_date.split('-'))
            current_date = datetime.date.today()
            try:
                due_date = datetime.date(current_date.year, month, day)
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date. Please use MM-DD format with valid month and day.", ephemeral=True)
                return
            if due_date < current_date:
                due_date = datetime.date(current_date.year + 1, month, day)

        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use MM-DD (e.g., 07-15 for July 15).",
                                                    ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if user_id not in self.tasks:
            self.tasks[user_id] = []

        self.tasks[user_id].append({"task": task, "due_date": due_date.isoformat(), "ignored_until": None})
        self.save_tasks()

        await interaction.response.send_message(f"Task '{task}' added with due date {due_date.strftime('%B %d, %Y')}.",
                                                ephemeral=True)

    @app_commands.command(name="view_tasks", description="View tasks for yourself or another user")
    @app_commands.describe(member="The member whose tasks you want to view (optional)")
    async def view_tasks(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        user_id = str(member.id)
        if user_id not in self.tasks or not self.tasks[user_id]:
            await interaction.response.send_message(f"No tasks found for {member.display_name}.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Tasks for {member.display_name}", color=discord.Color.blue())

        for task in self.tasks[user_id]:
            due_date = datetime.date.fromisoformat(task['due_date'])
            days_left = (due_date - datetime.date.today()).days

            if days_left < 0:
                status = "Overdue"
            elif days_left == 0:
                status = "Due today"
            else:
                status = f"{days_left} day{'s' if days_left != 1 else ''} left"

            embed.add_field(name=task['task'], value=f"Due: {task['due_date']} ({status})", inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        if user_id not in self.tasks:
            return

        tasks_to_remind = []
        for task in self.tasks[user_id]:
            due_date = datetime.date.fromisoformat(task['due_date'])
            days_left = (due_date - datetime.date.today()).days
            ignored_until = task.get('ignored_until')

            if 0 <= days_left <= 5 and (
                    ignored_until is None or datetime.datetime.now() > datetime.datetime.fromisoformat(ignored_until)):
                tasks_to_remind.append((task['task'], days_left))

        if tasks_to_remind:
            await self.send_reminder(message.author, tasks_to_remind)

    async def send_reminder(self, user, tasks):
        embed = discord.Embed(title="Task Reminders", color=discord.Color.blue())
        for task, days_left in tasks:
            embed.add_field(name=task, value=f"{days_left} day{'s' if days_left != 1 else ''} left", inline=False)

        view = ReminderView(self, user.id, [task for task, _ in tasks])
        try:
            await user.send(f"You have upcoming tasks!", embed=embed, view=view)
        except discord.Forbidden:
            # If DM is not possible, send to the last channel the user messaged in
            channel = self.bot.get_channel(user.last_message.channel.id)
            await channel.send(f"{user.mention}, I couldn't send you a DM. Here are your task reminders:", embed=embed,
                               view=view)

    @app_commands.command(name="delete_task", description="Delete one of your tasks")
    async def delete_task(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in self.tasks or not self.tasks[user_id]:
            await interaction.response.send_message("You have no tasks to delete.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=task['task'][:100], value=str(i))  # Truncate task name if too long
            for i, task in enumerate(self.tasks[user_id])
        ]

        view = TaskSelectView(self, user_id, options)
        await interaction.response.send_message("Select a task to delete:", view=view, ephemeral=True)


class TaskSelectView(discord.ui.View):
    def __init__(self, cog, user_id, options):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.add_item(TaskSelect(options))


class TaskSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a task to delete", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: TaskSelectView = self.view
        selected_task_index = int(self.values[0])
        selected_task = view.cog.tasks[view.user_id][selected_task_index]

        del view.cog.tasks[view.user_id][selected_task_index]
        if not view.cog.tasks[view.user_id]:
            del view.cog.tasks[view.user_id]
        view.cog.save_tasks()

        add_back_view = AddBackView(view.cog, view.user_id, selected_task)
        await interaction.response.edit_message(
            content=f"Task '{selected_task['task']}' was deleted.",
            view=add_back_view
        )


class AddBackView(discord.ui.View):
    def __init__(self, cog, user_id, task):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.task = task
        self.add_item(AddBackButton(cog, user_id, task))


class AddBackButton(discord.ui.Button):
    def __init__(self, cog, user_id, task):
        super().__init__(style=discord.ButtonStyle.success, label="Add it back")
        self.cog = cog
        self.user_id = user_id
        self.task = task

    async def callback(self, interaction: discord.Interaction):
        if self.user_id not in self.cog.tasks:
            self.cog.tasks[self.user_id] = []
        self.cog.tasks[self.user_id].append(self.task)
        self.cog.save_tasks()

        await interaction.response.edit_message(
            content=f"Task '{self.task['task']}' has been added back.",
            view=None
        )


class DeleteTaskView(discord.ui.View):
    def __init__(self, cog, user_id, options):
        super().__init__()
        self.selected_task = None
        self.cog = cog
        self.user_id = user_id
        self.add_item(SelectTask(options))

    @discord.ui.button(label="Confirm Deletion", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not hasattr(self, 'selected_task'):
            await interaction.response.send_message("Please select a task first.", ephemeral=True)
            return

        del self.cog.tasks[self.user_id][self.selected_task]
        if not self.cog.tasks[self.user_id]:
            del self.cog.tasks[self.user_id]
        self.cog.save_tasks()

        await interaction.response.send_message("Task deleted successfully.", ephemeral=True)
        self.stop()


class SelectTask(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a task to delete", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: DeleteTaskView = self.view
        view.selected_task = int(self.values[0])
        await interaction.response.send_message(f"Task selected. Click 'Confirm Deletion' to remove it.",
                                                ephemeral=True)


class ReminderView(discord.ui.View):
    def __init__(self, cog, user_id, tasks):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.tasks = tasks

    @discord.ui.button(label="Ignore for 1 hour", style=discord.ButtonStyle.secondary)
    async def ignore_hour_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        ignored_until = datetime.datetime.now() + datetime.timedelta(hours=1)
        for task in self.cog.tasks[str(self.user_id)]:
            if task['task'] in self.tasks:
                task['ignored_until'] = ignored_until.isoformat()

        self.cog.save_tasks()
        await interaction.response.send_message("Tasks ignored for the next hour.", ephemeral=True)

    @discord.ui.button(label="Ignore for today", style=discord.ButtonStyle.secondary)
    async def ignore_day_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        ignored_until = datetime.datetime.now() + datetime.timedelta(days=1)
        for task in self.cog.tasks[str(self.user_id)]:
            if task['task'] in self.tasks:
                task['ignored_until'] = ignored_until.isoformat()

        self.cog.save_tasks()
        await interaction.response.send_message("Tasks ignored for the next 24 hours.", ephemeral=True)

    @discord.ui.button(label="Mark as done", style=discord.ButtonStyle.success)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        user_tasks = self.cog.tasks[str(self.user_id)]
        self.cog.tasks[str(self.user_id)] = [task for task in user_tasks if task['task'] not in self.tasks]
        self.cog.save_tasks()
        await interaction.response.send_message("Tasks marked as done and removed from reminders.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TaskReminder(bot))
    print("- task_reminder.py loaded - ")
