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
intents.messages = True


def get_prefix(bot, message):
    # Get the bot's role ID
    bot_role = next(
        (role for role in message.guild.roles if role.name.lower() == "meteorix"), None
    )
    bot_role_id = bot_role.id if bot_role else None

    # Return all valid prefix formats
    return [
        f"<@{bot.user.id}> ",  # User mention
        f"<@!{bot.user.id}> ",  # Nickname mention
        f"<@&{bot_role_id}> " if bot_role_id else None,  # Role mention
        "@meteorix ",  # Plain text mention
    ]


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
        if command_name not in VALID_COMMANDS:
            error_message = f"""❌ Command `{command_name}` not found.

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

Try `@meteorix help` for more information."""
            await ctx.send(error_message)
            return

        # Command-specific help
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
--------------------------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
--------------------------------------------------------------------------------

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

**Examples:**
`@meteorix help upload` - Show upload command help
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix head` - Show earliest logged timestamp
`@meteorix head 2024_03_20` - Show first 5 rows of specific date
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


@bot.command(name="head")
@check_channel()
async def head(ctx, date=None):
    if date:
        await run_cli_command(ctx, ["head", date])
    else:
        await run_cli_command(ctx, ["head"])


@bot.command(name="tail")
@check_channel()
async def tail(ctx, date=None):
    if date:
        await run_cli_command(ctx, ["tail", date])
    else:
        await run_cli_command(ctx, ["tail"])


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


@bot.tree.command(name="who", description="Show information about the bot")
@app_commands.check(check_channel_slash)
async def who_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["who"])


@bot.tree.command(name="head", description="Show first 5 rows of data")
@app_commands.describe(date="Optional: Date to show data for (YYYY_MM_DD)")
@app_commands.check(check_channel_slash)
async def head_slash(interaction: discord.Interaction, date: str = None):
    if date:
        await run_cli_command_slash(interaction, ["head", date])
    else:
        await run_cli_command_slash(interaction, ["head"])


@bot.tree.command(name="tail", description="Show last 5 rows of data")
@app_commands.describe(date="Optional: Date to show data for (YYYY_MM_DD)")
@app_commands.check(check_channel_slash)
async def tail_slash(interaction: discord.Interaction, date: str = None):
    if date:
        await run_cli_command_slash(interaction, ["tail", date])
    else:
        await run_cli_command_slash(interaction, ["tail"])


VALID_COMMANDS = [
    "info",
    "upload",
    "delete",
    "eda",
    "ml",
    "check",
    "who",
    "help",
    "head",
    "tail",
]


def get_command_description(cmd):
    descriptions = {
        "info": "Show available date range",
        "upload": "Upload weather data",
        "delete": "Delete all weather data",
        "eda": "Run exploratory data analysis",
        "ml": "Run machine learning analysis",
        "check": "Check database collections",
        "who": "Show bot information",
        "help": "Show help information",
        "head": "Show first 5 rows of data",
        "tail": "Show last 5 rows of data",
    }
    return descriptions.get(cmd, "")


@bot.tree.command(name="help", description="Show help information")
@app_commands.describe(command_name="Select a command to get specific help for")
@app_commands.choices(
    command_name=[
        app_commands.Choice(name=f"{cmd} - {get_command_description(cmd)}", value=cmd)
        for cmd in VALID_COMMANDS
    ]
)
@app_commands.check(check_channel_slash)
async def help_slash(interaction: discord.Interaction, command_name: str = None):
    await interaction.response.defer()

    if command_name:
        if command_name not in VALID_COMMANDS:
            error_message = f"""❌ Command `{command_name}` not found.

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

Try `/help` for more information."""
            await interaction.followup.send(error_message)
            return

        # If the command is "help", show the general help menu
        if command_name == "help":
            help_text = """
--------------------------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
--------------------------------------------------------------------------------

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

**Examples:**
`/help upload` - Show upload command help
`/upload 2024_03_20` - Upload single date
`/upload 2024_03_20 2024_03_25` - Upload date range
`/head` - Show earliest logged timestamp
`/head 2024_03_20` - Show first 5 rows of specific date
`/who` - Show bot information"""
            await interaction.followup.send(help_text)
            return

        # Command-specific help for other commands
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["meteorix", command_name, "--help"]
            try:
                cli_main()
            except SystemExit:
                pass
        help_text = f.getvalue()
        await interaction.followup.send(f"```\n{help_text}\n```")
    else:
        # General help
        help_text = """
--------------------------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
--------------------------------------------------------------------------------

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command

**Examples:**
`/help upload` - Show upload command help
`/upload 2024_03_20` - Upload single date
`/upload 2024_03_20 2024_03_25` - Upload date range
`/head` - Show earliest logged timestamp
`/head 2024_03_20` - Show first 5 rows of specific date
`/who` - Show bot information"""
        await interaction.followup.send(help_text)


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

        if attempted_command == "help":
            # Check if there's an invalid subcommand for help
            args = ctx.message.content.split()[2:]
            if args:
                await ctx.send(f"❌ Command `{args[0]}` not found.")
                return

        # Show the standard error message with available commands
        error_message = f"""❌ Command `{attempted_command}` not found.

**Available Commands:**
• `info` - Show available date range
• `upload <start_date> [end_date]` - Upload weather data (format: YYYY_MM_DD)
• `delete` - Delete all weather data
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `check` - Check database collections
• `who` - Show information about the bot
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


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Get the bot's role ID (assuming the role has the same name as the bot)
    bot_role = next(
        (role for role in message.guild.roles if role.name.lower() == "meteorix"), None
    )
    bot_role_id = bot_role.id if bot_role else None

    # Check for mentions in multiple ways
    is_mentioned = (
        bot.user.id in [m.id for m in message.mentions]  # Direct mentions
        or f"<@{bot.user.id}>" in message.content  # Raw mention format
        or f"<@!{bot.user.id}>" in message.content  # Nickname mention format
        or (
            bot_role_id and f"<@&{bot_role_id}>" in message.content
        )  # Role mention format
        or message.content.lower().startswith("@meteorix")  # Plain text mention
    )

    if is_mentioned:
        # If it's just a mention with no command, send a greeting
        if message.content.strip() in [
            f"<@{bot.user.id}>",
            f"<@!{bot.user.id}>",
            f"<@&{bot_role_id}>" if bot_role_id else None,
            "@meteorix",
        ]:
            greeting = """👋 Hi there! I'm Meteorix, your weather data assistant.Try `@meteorix help` to see what I can do!"""
            await message.channel.send(greeting)
            return

        # Process commands if there are any
        await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    # Ignore edits from the bot itself
    if after.author == bot.user:
        return

    # Check for mentions in multiple ways
    is_mentioned = (
        bot.user.id in [m.id for m in after.mentions]  # Direct mentions
        or f"<@{bot.user.id}>" in after.content  # Raw mention format
        or f"<@!{bot.user.id}>" in after.content  # Nickname mention format
    )

    if is_mentioned:
        # Process the edited message as a command
        await bot.process_commands(after)


# Remove the old message handlers if they exist
if hasattr(bot, "_old_on_message"):
    bot.remove_listener(bot._old_on_message)
if hasattr(bot, "_old_on_message_edit"):
    bot.remove_listener(bot._old_on_message_edit)

# Store the new handlers
bot._old_on_message = on_message
bot._old_on_message_edit = on_message_edit


def run_bot():
    root_dir = Path(__file__).parent.parent
    secrets_path = root_dir / ".streamlit" / "secrets.toml"

    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
    token = secrets["bot_token"]["token"]
    bot.run(token)


if __name__ == "__main__":
    run_bot()
