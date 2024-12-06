import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import discord
import toml
from discord import app_commands
from discord.ext import commands

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_cli import main as cli_main  # noqa: E402

# Set up the bot with required intents
intents = discord.Intents.default()
intents.message_content = True


def get_prefix(bot, message):
    # This returns the bot's mention as a valid prefix
    return [f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]


class MeteorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, intents=intents, help_command=None)

    async def setup_hook(self):
        # This will sync the slash commands with Discord
        await self.tree.sync()
        print("Slash commands synced!")


bot = MeteorBot()

# Load channel ID from secrets
with open(Path(__file__).parent.parent / ".streamlit" / "secrets.toml", "r") as f:
    secrets = toml.load(f)
ALLOWED_CHANNEL_ID = int(secrets["channel_id"]["id"])


# Separate checks for message commands and slash commands
def check_channel():
    async def predicate(ctx):
        if ctx.channel.id != ALLOWED_CHANNEL_ID:
            await ctx.send(
                f"❌ This command can only be used in <#{ALLOWED_CHANNEL_ID}>"
            )
            return False
        return True

    return commands.check(predicate)


def check_channel_slash(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return False
    return True


@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if channel:
        print(f"Listening in channel: #{channel.name}")
    else:
        print(f"Warning: Could not find channel with ID {ALLOWED_CHANNEL_ID}")


# Message-based commands
@bot.command(name="help")
@check_channel()
async def help_command(ctx, command_name=None):
    if command_name:
        # Command-specific help
        try:
            with redirect_stdout(io.StringIO()):
                sys.argv = ["meteorix", command_name, "--help"]
                cli_main()
        except SystemExit:
            # Capture the help output by redirecting stderr
            f = io.StringIO()
            with redirect_stdout(f):
                sys.argv = ["meteorix", command_name, "--help"]
                try:
                    cli_main()
                except SystemExit:
                    pass
            help_text = f.getvalue()
            await ctx.send(f"```\n{help_text}\n```")
    else:
        # General help
        help_text = """
**Meteorix Weather Bot Commands**
Use `@meteorix help <command>` for detailed help on a specific command.

Available Commands:
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot and its creators
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

Examples:
`@meteorix help upload` - Show upload command help
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix who` - Show bot information
"""
        await ctx.send(help_text)


@bot.command(name="info")
@check_channel()
async def info(ctx):
    await run_cli_command(ctx, ["info"])


@bot.command(name="upload")
@check_channel()
async def upload(ctx, start_date, end_date=None):
    if end_date:
        await run_cli_command(ctx, ["upload", start_date, end_date])
    else:
        await run_cli_command(ctx, ["upload", start_date])


@bot.command(name="delete")
@check_channel()
async def delete(ctx):
    await run_cli_command(ctx, ["delete"])


@bot.command(name="eda")
@check_channel()
async def eda(ctx):
    await run_cli_command(ctx, ["eda"])


@bot.command(name="ml")
@check_channel()
async def ml(ctx):
    await run_cli_command(ctx, ["ml"])


@bot.command(name="check")
@check_channel()
async def check(ctx):
    await run_cli_command(ctx, ["check"])


@bot.command(name="who")
@check_channel()
async def who(ctx):
    await run_cli_command(ctx, ["who"])


# Slash commands
@bot.tree.command(name="info", description="Show available date range")
@app_commands.check(check_channel_slash)
async def info_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["info"])


@bot.tree.command(name="upload", description="Upload weather data (format: YYYY_MM_DD)")
@app_commands.describe(
    start_date="Start date in YYYY_MM_DD format",
    end_date="End date in YYYY_MM_DD format (optional)",
)
@app_commands.check(check_channel_slash)
async def upload_slash(
    interaction: discord.Interaction, start_date: str, end_date: str = None
):
    if end_date:
        await run_cli_command_slash(interaction, ["upload", start_date, end_date])
    else:
        await run_cli_command_slash(interaction, ["upload", start_date])


@bot.tree.command(name="delete", description="Delete all weather data")
@app_commands.check(check_channel_slash)
async def delete_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["delete"])


@bot.tree.command(name="eda", description="Run exploratory data analysis")
@app_commands.check(check_channel_slash)
async def eda_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["eda"])


@bot.tree.command(name="ml", description="Run machine learning analysis")
@app_commands.check(check_channel_slash)
async def ml_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["ml"])


@bot.tree.command(name="check", description="Check database collections")
@app_commands.check(check_channel_slash)
async def check_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["check"])


@bot.tree.command(
    name="who", description="Show information about the bot and its creators"
)
@app_commands.check(check_channel_slash)
async def who_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["who"])


# Helper functions
async def run_cli_command(ctx, args):
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            sys.argv = ["meteorix"] + args
            cli_main()

        output = f.getvalue()

        if not output.strip():
            output = "Command completed successfully with no output."

        chunks = [output[i : i + 1900] for i in range(0, len(output), 1900)]

        for chunk in chunks:
            formatted_output = f"```\n{chunk}\n```"
            await ctx.send(formatted_output)

    except Exception as e:
        error_msg = f"```\nError: {str(e)}\n```"
        await ctx.send(error_msg)


async def run_cli_command_slash(interaction: discord.Interaction, args):
    await interaction.response.defer()

    f = io.StringIO()
    try:
        with redirect_stdout(f):
            sys.argv = ["meteorix"] + args
            cli_main()

        output = f.getvalue()

        if not output.strip():
            output = "Command completed successfully with no output."

        chunks = [output[i : i + 1900] for i in range(0, len(output), 1900)]

        first_chunk = chunks[0]
        await interaction.followup.send(f"```\n{first_chunk}\n```")

        for chunk in chunks[1:]:
            await interaction.channel.send(f"```\n{chunk}\n```")

    except Exception as e:
        await interaction.followup.send(f"```\nError: {str(e)}\n```")


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            f"❌ This command can only be used in <#{ALLOWED_CHANNEL_ID}>",
            ephemeral=True,
        )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Get the attempted command from the message
        attempted_command = (
            ctx.message.content.split()[1]
            if len(ctx.message.content.split()) > 1
            else "unknown"
        )

        error_message = f"""❌ Command `{attempted_command}` not found.

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot and its creators
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

Try `@meteorix help` for more information."""

        await ctx.send(error_message)
    elif isinstance(error, commands.CheckFailure):
        # Channel check failure is already handled
        pass
    else:
        # Handle other errors
        await ctx.send(f"```\nError: {str(error)}\n```")


def run_bot():
    root_dir = Path(__file__).parent.parent
    secrets_path = root_dir / ".streamlit" / "secrets.toml"

    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
    token = secrets["bot_token"]["token"]
    bot.run(token)


if __name__ == "__main__":
    run_bot()
