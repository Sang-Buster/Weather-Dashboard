import colorama
from colorama import Fore, Style


def print_banner():
    colorama.init()
    lines = [
        f"{Fore.LIGHTBLUE_EX}███╗░░░███╗███████╗████████╗███████╗░█████╗░██████╗░██╗██╗░░██╗",
        f"{Fore.LIGHTBLUE_EX}████╗░████║██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██║╚██╗██╔╝",
        f"{Fore.LIGHTBLUE_EX}██╔████╔██║█████╗░░░░░██║░░░█████╗░░██║░░██║██████╔╝██║░╚███╔╝░",
        f"{Fore.LIGHTBLUE_EX}██║╚██╔╝██║██╔══╝░░░░░██║░░░██╔══╝░░██║░░██║██╔══██╗██║░██╔██╗░",
        f"{Fore.LIGHTBLUE_EX}██║░╚═╝░██║███████╗░░░██║░░░███████╗╚█████╔╝██║░░██║██║██╔╝╚██╗",
        f"{Fore.LIGHTBLUE_EX}╚═╝░░░░░╚═╝╚══════╝░░░╚═╝░░░╚══════╝░╚════╝░╚═╝░░╚═╝╚═╝╚═╝░░╚═╝",
        f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}---------------------------------------------------------------",
        f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎",
        f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}---------------------------------------------------------------{Style.RESET_ALL}",
    ]

    for line in lines:
        print(line)


def print_usage(usage_text):
    print(f"{Fore.YELLOW}Usage:{Style.RESET_ALL} {usage_text}\n")
