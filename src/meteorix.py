import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from datetime import datetime
import streamlit as st
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli import main as cli_main  # noqa: E402
from cli_components.plot import create_weather_plot  # noqa: E402
from cli_components.monitor import (  # noqa: E402
    toggle_monitor,
    check_data_freshness,
    get_monitor_config,
)
from cli_components import (  # noqa: E402
    get_available_models,
    handle_chat_command,
)

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


ALLOWED_CHANNEL_IDS = [
    int(channel_id) for channel_id in st.secrets["channel_id"].values()
]


# Update the channel check functions
def check_channel():
    async def predicate(ctx):
        if ctx.channel.id not in ALLOWED_CHANNEL_IDS:
            allowed_channels = [
                f"<#{channel_id}>" for channel_id in ALLOWED_CHANNEL_IDS
            ]
            await ctx.send(
                f"❌ This command can only be used in: {', '.join(allowed_channels)}"
            )
            return False
        return True

    return commands.check(predicate)


def check_channel_slash(interaction: discord.Interaction):
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        return False
    return True


@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    for channel_id in ALLOWED_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"Listening in channel: #{channel.name}")
        else:
            print(f"Warning: Could not find channel with ID {channel_id}")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Start the monitoring task
    bot.loop.create_task(check_data_collection())


# Message-based commands
@bot.command(name="help")
@check_channel()
async def help_command(ctx, command_name=None):
    if command_name:
        # Special case for "help" command
        if command_name == "help":
            help_text_1 = """
---------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
---------------------------------------------------------------

**Available Commands:**
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
• `who` - Show information about the bot
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command"""

            help_text_2 = """
**Examples:**
`@meteorix help upload` - Show upload command help
`@meteorix upload` - Upload last 3 days
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix delete` - Delete all data
`@meteorix delete 2024_03_20` - Delete single date
`@meteorix delete 2024_03_20 2024_03_25` - Delete date range
`@meteorix head` - Show earliest logged timestamp
`@meteorix head 2024_03_20` - Show first 5 rows of specific date
`@meteorix plot 2024_03_20` - Generate plot for single date
`@meteorix who` - Show bot information
`@meteorix monitor enable` - Enable data collection monitoring
`@meteorix monitor disable` - Disable data collection monitoring
`@meteorix monitor status` - Check current monitoring status
`@meteorix freq 0` - Set to low frequency mode (1Hz)
`@meteorix freq 1` - Set to high frequency mode (32Hz)
`@meteorix freq status` - Check current frequency mode
`@meteorix ifconfig` - Show Pi network status
`@meteorix top` - Show Pi system status"""

            # Send both parts
            await ctx.send(help_text_1)
            await ctx.send(help_text_2)
            return

        if command_name not in VALID_COMMANDS:
            error_message = f"""❌ Command `{command_name}` not found.

**Available Commands:**
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
• `who` - Show information about the bot
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
        # Split the help message into multiple parts
        help_text_1 = """
---------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
---------------------------------------------------------------

**Available Commands:**
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
• `who` - Show information about the bot
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command"""

        help_text_2 = """
**Examples:**
`@meteorix help upload` - Show upload command help
`@meteorix upload` - Upload last 3 days
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix delete` - Delete all data
`@meteorix delete 2024_03_20` - Delete single date
`@meteorix delete 2024_03_20 2024_03_25` - Delete date range
`@meteorix head` - Show earliest logged timestamp
`@meteorix head 2024_03_20` - Show first 5 rows of specific date
`@meteorix plot 2024_03_20` - Generate plot for single date
`@meteorix who` - Show bot information
`@meteorix monitor enable` - Enable data collection monitoring
`@meteorix monitor disable` - Disable data collection monitoring
`@meteorix monitor status` - Check current monitoring status
`@meteorix freq 0` - Set to low frequency mode (1Hz)
`@meteorix freq 1` - Set to high frequency mode (32Hz)
`@meteorix freq status` - Check current frequency mode
`@meteorix ifconfig` - Show Pi network status
`@meteorix top` - Show Pi system status"""

        # Send both parts
        await ctx.send(help_text_1)
        await ctx.send(help_text_2)


@bot.command(name="upload")
@check_channel()
async def upload(ctx, start_date=None, end_date=None):
    if end_date:
        await run_cli_command(ctx, ["upload", start_date, end_date])
    elif start_date:
        await run_cli_command(ctx, ["upload", start_date])
    else:
        await run_cli_command(ctx, ["upload"])


@bot.command(name="delete")
@check_channel()
async def delete(ctx, start_date=None, end_date=None):
    if end_date:
        await run_cli_command(ctx, ["delete", start_date, end_date])
    elif start_date:
        await run_cli_command(ctx, ["delete", start_date])
    else:
        await run_cli_command(ctx, ["delete"])


@bot.command(name="check")
@check_channel()
async def check(ctx):
    await run_cli_command(ctx, ["check"])


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


@bot.command(name="info")
@check_channel()
async def info(ctx, month=None):
    if month:
        await run_cli_command(ctx, ["info", month])
    else:
        await run_cli_command(ctx, ["info"])


@bot.command(name="spit")
@check_channel()
async def spit(ctx, start_date, end_date=None):
    if end_date:
        await run_cli_command(ctx, ["spit", start_date, end_date])
    else:
        await run_cli_command(ctx, ["spit", start_date])


@bot.command(name="eda")
@check_channel()
async def eda(ctx):
    await run_cli_command(ctx, ["eda"])


@bot.command(name="ml")
@check_channel()
async def ml(ctx):
    await run_cli_command(ctx, ["ml"])


@bot.command(name="who")
@check_channel()
async def who(ctx):
    await run_cli_command(ctx, ["who"])


@bot.command(name="plot")
@check_channel()
async def plot(ctx, start_date, end_date=None):
    try:
        # Generate plots in memory only (bypass CLI completely)
        filenames, plot_buffers, _ = create_weather_plot(
            start_date, end_date, save_locally=False
        )

        files = [
            discord.File(fp=buffer, filename=fname)
            for fname, buffer in zip(filenames, plot_buffers)
        ]

        await ctx.send(
            f"📊 Weather plots for {start_date}"
            + (f" to {end_date}" if end_date else ""),
            files=files,
        )
    except Exception as e:
        await ctx.send(f"Error creating plots: {str(e)}")


@bot.command(name="monitor")
@check_channel()
async def monitor_command(ctx, action=None):
    """Monitor data collection status"""
    if not action:
        await ctx.send("❌ Please specify an action: `enable`, `disable`, or `status`")
        return

    if action.lower() not in ["enable", "disable", "status"]:
        await ctx.send("❌ Invalid action. Use `enable`, `disable`, or `status`")
        return

    # Capture the output from toggle_monitor
    f = io.StringIO()
    with redirect_stdout(f):
        toggle_monitor(action.lower())

    # Send the formatted output
    output = f.getvalue()
    if output:
        await ctx.send(f"```\n{output}\n```")


@bot.command(name="freq")
@check_channel()
async def freq_command(ctx, action=None, value=None):
    """Control data logging frequency"""
    if not action or action.lower() not in ["set", "status"]:
        await ctx.send("❌ Please specify an action: `set` or `status`")
        return

    if action.lower() == "set" and (not value or value not in ["0", "1"]):
        await ctx.send(
            "❌ For 'set' action, please specify frequency value: '0' (1Hz) or '1' (32Hz)"
        )
        return

    await run_cli_command(ctx, ["freq", action.lower()] + ([value] if value else []))


@bot.command(name="ifconfig")
@check_channel()
async def ifconfig(ctx):
    await run_cli_command(ctx, ["ifconfig"])


@bot.command(name="top")
@check_channel()
async def top(ctx):
    await run_cli_command(ctx, ["top"])


@bot.command(name="chat")
@check_channel()
async def chat_command(ctx, *, prompt=None):
    """Chat with the weather station AI assistant."""
    if not prompt:
        help_msg = (
            "Please provide a question or prompt. Examples:\n"
            '`meteorix chat "What\'s the temperature right now?"`\n'
            '`meteorix chat "How was the weather last week?"`\n'
            '`meteorix chat "Analyze weather from 2024_10_08 to 2024_10_10"`'
        )
        await ctx.send(help_msg)
        return

    try:
        # Create args object similar to CLI args
        class Args:
            def __init__(self, prompt, model=None):
                self.action_or_prompt = prompt
                self.model = model
                self.remaining_prompt = None

        args = Args(prompt)

        # Special handling for 'models' subcommand
        if prompt.strip().lower() == "models":
            # Get available models
            available_models = get_available_models()

            # Format the response
            response = "**Available Models:**\n"
            for model in available_models:
                response += f"• {model}\n"
            response += '\nUse with: `meteorix chat --model <model_name> "your prompt"`'

            await ctx.send(response)
            return

        # Get the coroutine from handle_chat_command
        coroutine = handle_chat_command(args)

        # Send typing indicator while processing
        async with ctx.typing():
            # Only await if it's a coroutine
            if coroutine is not None:
                response = await coroutine

                if response:
                    # Split long messages if needed
                    MAX_LENGTH = 2000
                    messages = [
                        response[i : i + MAX_LENGTH]
                        for i in range(0, len(response), MAX_LENGTH)
                    ]
                    for message in messages:
                        await ctx.send(message)
                else:
                    await ctx.send(
                        "Sorry, I couldn't process your request. Please try again."
                    )

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


# Slash commands
@bot.tree.command(name="info", description="Show available date range")
@app_commands.describe(month="Optional: Month to show statistics for (YYYY_MM)")
@app_commands.check(check_channel_slash)
async def info_slash(interaction: discord.Interaction, month: str = None):
    if month:
        await run_cli_command_slash(interaction, ["info", month])
    else:
        await run_cli_command_slash(interaction, ["info"])


@bot.tree.command(name="upload", description="Upload weather data to MongoDB")
@app_commands.describe(
    start_date="Start date in YYYY_MM_DD format (optional - defaults to last 3 days if not specified)",
    end_date="End date in YYYY_MM_DD format (optional)",
)
@app_commands.check(check_channel_slash)
async def upload_slash(
    interaction: discord.Interaction,
    start_date: str = None,  # Make start_date optional
    end_date: str = None,  # Make end_date optional
):
    if end_date:
        await run_cli_command_slash(interaction, ["upload", start_date, end_date])
    elif start_date:
        await run_cli_command_slash(interaction, ["upload", start_date])
    else:
        await run_cli_command_slash(interaction, ["upload"])  # No dates = last 3 days


@bot.tree.command(name="delete", description="Delete weather data from MongoDB")
@app_commands.describe(
    start_date="Start date in YYYY_MM_DD format (optional). If only start_date provided, deletes just that single day",
    end_date="End date in YYYY_MM_DD format (optional). Required only if deleting a date range",
)
@app_commands.check(check_channel_slash)
async def delete_slash(
    interaction: discord.Interaction,
    start_date: str = None,
    end_date: str = None,
):
    if end_date:
        await run_cli_command_slash(interaction, ["delete", start_date, end_date])
    elif start_date:
        await run_cli_command_slash(interaction, ["delete", start_date])
    else:
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


@bot.tree.command(
    name="spit",
    description="Retrieve and output raw CSV data for a specific date or date range",
)
@app_commands.describe(
    start_date="Start date (YYYY_MM_DD)",
    end_date="End date (YYYY_MM_DD, optional)",
)
@app_commands.check(check_channel_slash)
async def spit_slash(
    interaction: discord.Interaction, start_date: str, end_date: str = None
):
    if end_date:
        await run_cli_command_slash(interaction, ["spit", start_date, end_date])
    else:
        await run_cli_command_slash(interaction, ["spit", start_date])


@bot.tree.command(name="plot", description="Create weather data plots")
@app_commands.describe(
    start_date="Start date in YYYY_MM_DD format",
    end_date="End date in YYYY_MM_DD format (optional)",
)
@app_commands.check(check_channel_slash)
async def plot_slash(
    interaction: discord.Interaction, start_date: str, end_date: str = None
):
    if end_date:
        await run_cli_command_slash(interaction, ["plot", start_date, end_date])
    else:
        await run_cli_command_slash(interaction, ["plot", start_date])


@bot.tree.command(name="monitor", description="Monitor data collection status")
@app_commands.describe(action="Enable, disable, or check monitoring status")
@app_commands.choices(
    action=[
        app_commands.Choice(name="enable", value="enable"),
        app_commands.Choice(name="disable", value="disable"),
        app_commands.Choice(name="status", value="status"),
    ]
)
@app_commands.check(check_channel_slash)
async def monitor_slash(interaction: discord.Interaction, action: str):
    # Capture the output from toggle_monitor
    f = io.StringIO()
    with redirect_stdout(f):
        toggle_monitor(action)

    # Send the formatted output
    output = f.getvalue()
    await interaction.response.send_message(f"```\n{output}\n```")


@bot.tree.command(name="freq", description="Control data logging frequency")
@app_commands.describe(
    action="Action to perform: '0' (1Hz), '1' (32Hz), or 'status'",
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="1Hz (Low Frequency)", value="0"),
        app_commands.Choice(name="32Hz (High Frequency)", value="1"),
        app_commands.Choice(name="Check Status", value="status"),
    ],
)
@app_commands.check(check_channel_slash)
async def freq_slash(interaction: discord.Interaction, action: str):
    await run_cli_command_slash(interaction, ["freq", action])


@bot.tree.command(name="ifconfig", description="Show Raspberry Pi network information")
@app_commands.check(check_channel_slash)
async def ifconfig_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["ifconfig"])


@bot.tree.command(name="top", description="Show Raspberry Pi system status")
@app_commands.check(check_channel_slash)
async def top_slash(interaction: discord.Interaction):
    await run_cli_command_slash(interaction, ["top"])


@bot.tree.command(
    name="chat", description="Chat with an AI about weather data analysis"
)
@app_commands.describe(
    prompt="Your question about the weather data",
    model=f"AI model to use (default: {st.secrets['ollama']['model']})",
    date_range="Optional date range (e.g., from 2024_02_01 to 2024_02_14)",
)
@app_commands.choices(
    model=[
        app_commands.Choice(name=model_name, value=model_name)
        for model_name in get_available_models()
    ]
)
@app_commands.check(check_channel_slash)
async def chat_slash(
    interaction: discord.Interaction,
    prompt: str,
    model: str = None,
    date_range: str = None,
):
    # Defer the response since it might take a while
    await interaction.response.defer()

    try:
        # Special handling for 'models' subcommand
        if prompt.strip().lower() == "models":
            # Get available models
            available_models = get_available_models()

            # Format the response
            response = "**Available Models:**\n"
            for model in available_models:
                response += f"• {model}\n"
            response += '\nUse with: `meteorix chat --model <model_name> "your prompt"`'

            await interaction.followup.send(response)
            return

        # Create args object
        class Args:
            def __init__(self, prompt, model=None):
                self.action_or_prompt = prompt
                self.model = model
                self.remaining_prompt = None

        args = Args(prompt, model)

        # Get and await the coroutine
        coroutine = handle_chat_command(args)

        # Only await if it's a coroutine
        if coroutine is not None:
            response = await coroutine

            if response:
                # Split long messages if needed
                MAX_LENGTH = 2000
                messages = [
                    response[i : i + MAX_LENGTH]
                    for i in range(0, len(response), MAX_LENGTH)
                ]

                # Send first message as followup
                await interaction.followup.send(messages[0])

                # Send remaining messages if any
                for message in messages[1:]:
                    await interaction.channel.send(message)
            else:
                await interaction.followup.send(
                    "Sorry, I couldn't process your request. Please try again."
                )
        else:
            await interaction.followup.send(
                "Sorry, I couldn't process your request. Please try again."
            )

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}")


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
    "spit",
    "plot",
    "monitor",
    "freq",
    "ifconfig",
    "top",
    "chat",  # Add chat command
]


def get_command_description(cmd):
    """Get the description for a command."""
    descriptions = {
        "info": "Show available date range and file statistics",
        "upload": "Upload weather data to MongoDB",
        "delete": "Delete all weather data from MongoDB",
        "eda": "Run exploratory data analysis",
        "ml": "Run machine learning analysis",
        "check": "Check database collections",
        "who": "Show bot information",
        "help": "Show help information",
        "head": "Show first 5 rows of data",
        "tail": "Show last 5 rows of data",
        "spit": "Get raw CSV data for specified dates",
        "plot": "Create weather data plots",
        "monitor": "Monitor data collection status",
        "freq": "Control data logging frequency (0=1Hz, 1=32Hz)",
        "ifconfig": "Show Raspberry Pi network information",
        "top": "Show Raspberry Pi system status",
        "chat": "Chat with an AI about weather data analysis",  # Add chat description
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
        # Special case for "help" command
        if command_name == "help":
            help_text_1 = """
---------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
---------------------------------------------------------------

**Available Commands:**
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
• `who` - Show information about the bot
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command"""

            help_text_2 = """
**Examples:**
`@meteorix help upload` - Show upload command help
`@meteorix upload` - Upload last 3 days
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix delete` - Delete all data
`@meteorix delete 2024_03_20` - Delete single date
`@meteorix delete 2024_03_20 2024_03_25` - Delete date range
`@meteorix head` - Show earliest logged timestamp
`@meteorix head 2024_03_20` - Show first 5 rows of specific date
`@meteorix plot 2024_03_20` - Generate plot for single date
`@meteorix who` - Show bot information
`@meteorix monitor enable` - Enable data collection monitoring
`@meteorix monitor disable` - Disable data collection monitoring
`@meteorix monitor status` - Check current monitoring status
`@meteorix freq 0` - Set to low frequency mode (1Hz)
`@meteorix freq 1` - Set to high frequency mode (32Hz)
`@meteorix freq status` - Check current frequency mode
`@meteorix ifconfig` - Show Pi network status
`@meteorix top` - Show Pi system status"""

            # Send both parts
            await interaction.followup.send(help_text_1)
            await interaction.followup.send(help_text_2)
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
        return

    # If no specific command requested, show the general help menu
    help_text_1 = """
---------------------------------------------------------------
      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎
---------------------------------------------------------------

**Available Commands:**
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
• `who` - Show information about the bot
• `help` - Show this help message
• `help <command>` - Show detailed help for a specific command"""

    help_text_2 = """
**Examples:**
`@meteorix help upload` - Show upload command help
`@meteorix upload` - Upload last 3 days
`@meteorix upload 2024_03_20` - Upload single date
`@meteorix upload 2024_03_20 2024_03_25` - Upload date range
`@meteorix delete` - Delete all data
`@meteorix delete 2024_03_20` - Delete single date
`@meteorix delete 2024_03_20 2024_03_25` - Delete date range
`@meteorix head` - Show earliest logged timestamp
`@meteorix head 2024_03_20` - Show first 5 rows of specific date
`@meteorix plot 2024_03_20` - Generate plot for single date
`@meteorix who` - Show bot information
`@meteorix monitor enable` - Enable data collection monitoring
`@meteorix monitor disable` - Disable data collection monitoring
`@meteorix monitor status` - Check current monitoring status
`@meteorix freq 0` - Set to low frequency mode (1Hz)
`@meteorix freq 1` - Set to high frequency mode (32Hz)
`@meteorix freq status` - Check current frequency mode
`@meteorix ifconfig` - Show Pi network status
`@meteorix top` - Show Pi system status"""

    # Send both parts
    await interaction.followup.send(help_text_1)
    await interaction.followup.send(help_text_2)


# Helper functions
async def run_cli_command(ctx, args):
    try:
        # For plot command, bypass cli_main entirely and use create_weather_plot directly
        if args[0] == "plot":
            # Generate plots in memory
            filenames, plot_buffers, _ = create_weather_plot(
                args[1], args[2] if len(args) > 2 else None
            )

            # Create discord.File objects directly from memory buffers
            files = [
                discord.File(fp=buffer, filename=fname)
                for fname, buffer in zip(filenames, plot_buffers)
            ]

            await ctx.send(
                f"📊 Weather plots for {args[1]}"
                + (f" to {args[2]}" if len(args) > 2 else ""),
                files=files,
            )
            return  # Ensure the function exits here to prevent further processing

        # For other commands, use the normal CLI output handling
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["meteorix"] + args
            cli_main()

        # Rest of the command handling...
        output = f.getvalue()
        if not output.strip():
            output = "Command completed successfully with no output."

        if args[0] == "spit":
            temp_file = io.StringIO(output)
            file = discord.File(
                fp=temp_file,
                filename=f"output_spit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )
            await ctx.send("Here's the CSV data:", file=file)
        elif len(output) > 1900 and args[0] not in ["head", "tail"]:
            temp_file = io.StringIO(output)
            file = discord.File(
                fp=temp_file,
                filename=f"output_{args[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            )
            await ctx.send(
                "Output was too long to display directly. Here's the complete output:",
                file=file,
            )
        else:
            formatted_output = f"```\n{output}\n```"
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
            if args[0] == "plot":
                # For plot command, only get the plots without running CLI output
                filenames, plot_buffers, _ = create_weather_plot(
                    args[1], args[2] if len(args) > 2 else None
                )
            else:
                cli_main()

        output = f.getvalue()

        if not output.strip():
            output = "Command completed successfully with no output."

        # For plot command, send all generated images
        if args[0] == "plot":
            # Create discord.File objects for each plot
            files = [
                discord.File(fp=buffer, filename=fname)
                for fname, buffer in zip(filenames, plot_buffers)
            ]

            await interaction.followup.send(
                f"📊 Weather plots for {args[1]}"
                + (f" to {args[2]}" if len(args) > 2 else ""),
                files=files,
            )
        # For spit command, always send as file
        elif args[0] == "spit":
            temp_file = io.StringIO(output)
            file = discord.File(
                fp=temp_file,
                filename=f"output_spit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )
            await interaction.followup.send(
                "Here's the CSV data:",
                file=file,
            )
        # For very long outputs (except head/tail), send as file
        elif len(output) > 1900 and args[0] not in ["head", "tail"]:
            temp_file = io.StringIO(output)
            file = discord.File(
                fp=temp_file,
                filename=f"output_{args[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            )
            await interaction.followup.send(
                "Output was too long to display directly. Here's the complete output:",
                file=file,
            )
        else:
            # Use fixed-width formatting for all outputs
            formatted_output = f"```\n{output}\n```"
            await interaction.followup.send(formatted_output)

    except Exception as e:
        error_msg = f"```\nError: {str(e)}\n```"
        await interaction.followup.send(error_msg)


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CheckFailure):
        allowed_channels = [f"<#{channel_id}>" for channel_id in ALLOWED_CHANNEL_IDS]
        await interaction.response.send_message(
            f"❌ This command can only be used in: {', '.join(allowed_channels)}",
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
• `upload [start_date] [end_date]` - Upload weather data to database
• `delete [start_date] [end_date]` - Delete weather data from database
• `check` - Check database collections
• `head [date]` - Show earliest logged timestamp or first 5 rows if date specified
• `tail [date]` - Show latest logged timestamp or last 5 rows if date specified
• `info [month]` - Show available date range and file statistics for a specific month (format: YYYY_MM)
• `spit <start_date> [end_date]` - Get raw CSV data for specified dates
• `eda` - Run exploratory data analysis
• `ml` - Run machine learning analysis
• `plot <start_date> [end_date]` - Generate weather plots for specified dates
• `monitor <action>` - Monitor data collection status (action: enable, disable, status)
• `freq <action>` - Control data logging frequency (action: 0=1Hz, 1=32Hz, status)
• `ifconfig` - Show Raspberry Pi network information
• `top` - Show Raspberry Pi system status
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
            greeting = """ Hi there! I'm Meteorix, your weather data assistant. Try `@meteorix help` to see what I can do!"""
            await message.channel.send(greeting)
            return

        # Process commands if there are any
        await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    # Ignore edits from the bot itself
    if after.author == bot.user:
        return

    # Get the bot's role ID (assuming the role has the same name as the bot)
    bot_role = next(
        (role for role in after.guild.roles if role.name.lower() == "meteorix"), None
    )
    bot_role_id = bot_role.id if bot_role else None

    # Check for mentions in multiple ways
    is_mentioned = (
        bot.user.id in [m.id for m in after.mentions]  # Direct mentions
        or f"<@{bot.user.id}>" in after.content  # Raw mention format
        or f"<@!{bot.user.id}>" in after.content  # Nickname mention format
        or (
            bot_role_id and f"<@&{bot_role_id}>" in after.content
        )  # Role mention format
        or after.content.lower().startswith("@meteorix")  # Plain text mention
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
    token = st.secrets["bot_token"]["token"]
    bot.run(token)


# Add monitoring task
async def check_data_collection():
    """Background task to monitor data collection"""
    await bot.wait_until_ready()

    last_alert_time = {}  # Store last alert time per channel
    alert_cooldown = 900  # Send alert every 15 minutes

    while not bot.is_closed():
        try:
            config = get_monitor_config()

            if config["enabled"]:
                fresh, latest_time = check_data_freshness()

                if not fresh:
                    current_time = datetime.now()

                    for channel_id in ALLOWED_CHANNEL_IDS:
                        # Check if enough time has passed since last alert
                        if (
                            channel_id not in last_alert_time
                            or (
                                current_time - last_alert_time[channel_id]
                            ).total_seconds()
                            >= alert_cooldown
                        ):
                            channel = bot.get_channel(channel_id)
                            if channel:
                                time_str = (
                                    latest_time.strftime("%Y-%m-%d %H:%M:%S")
                                    if latest_time
                                    else "N/A"
                                )
                                await channel.send(
                                    f"⚠️ **Alert**: No new data collected in the last {config['alert_threshold_minutes']} minutes!\n"
                                    f"Latest data point: {time_str}"
                                )
                                last_alert_time[channel_id] = current_time

            # Use the configured check interval
            await asyncio.sleep(config["check_interval_minutes"] * 60)

        except Exception as e:
            print(f"Error in monitoring task: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before retrying if there's an error


if __name__ == "__main__":
    run_bot()
