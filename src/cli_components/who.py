from rich import print as rprint


def show_who_info():
    """Show information about the bot and its creators"""
    info = {
        "Version": "1.0",
        "Created By": ["Sang Xing"],
        "Basic Usage": "Type `@meteorix help`",
        "Repository": "https://github.com/Sang-Buster/weather-dashboard",
    }

    rprint("[bold blue]Bot Information:[/bold blue]")
    for key, value in info.items():
        if isinstance(value, list):
            rprint(f"[yellow]{key}:[/yellow] {', '.join(value)}")
        else:
            rprint(f"[yellow]{key}:[/yellow] {value}")
