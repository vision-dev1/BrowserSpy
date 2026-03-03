"""
BrowserSpy — Banner module.
Displays the ASCII art banner and author information on startup.
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

console = Console()

BANNER_ART = r"""
██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗███████╗██████╗ ███████╗██████╗ ██╗   ██╗
██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔════╝██╔══██╗██╔════╝██╔══██╗╚██╗ ██╔╝
██████╔╝██████╔╝██║   ██║██║ █╗ ██║███████╗█████╗  ██████╔╝███████╗██████╔╝ ╚████╔╝ 
██╔══██╗██╔══██╗██║   ██║██║███╗██║╚════██║██╔══╝  ██╔══██╗╚════██║██╔═══╝   ╚██╔╝  
██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║███████╗██║  ██║███████║██║        ██║   
╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝        ╚═╝   
"""

VERSION = "1.0.0"
AUTHOR = "vision-dev1"
GITHUB = "https://github.com/vision-dev1"
PORTFOLIO = "https://visionkc.com.np"
TAGLINE = "Spy on your browser before someone else does."

DISCLAIMER = (
    "[!] BrowserSpy is intended for educational and forensic purposes only.\n"
    "    Only use on systems you own or have explicit written permission to analyze.\n"
    "    Unauthorized use is illegal and unethical."
)


def print_banner(no_banner: bool = False) -> None:
    """
    Print the BrowserSpy ASCII art banner and author information.

    Args:
        no_banner: If True, suppress the banner output.
    """
    if no_banner:
        return

    banner_text = Text(BANNER_ART, style="bold cyan")
    console.print(banner_text)

    info_line = (
        f"  [bold yellow]{TAGLINE}[/bold yellow]\n"
        f"  [dim]Version:[/dim] [cyan]{VERSION}[/cyan]  "
        f"[dim]|[/dim]  [dim]Author:[/dim] [green]{AUTHOR}[/green]\n"
        f"  [dim]GitHub:[/dim]  [link={GITHUB}][blue]{GITHUB}[/blue][/link]  "
        f"[dim]|[/dim]  [dim]Portfolio:[/dim] [link={PORTFOLIO}][blue]{PORTFOLIO}[/blue][/link]"
    )
    console.print(info_line)
    console.print()

    disclaimer_panel = Panel(
        f"[bold yellow]{DISCLAIMER}[/bold yellow]",
        border_style="yellow",
        expand=False,
    )
    console.print(Align.center(disclaimer_panel))
    console.print()
