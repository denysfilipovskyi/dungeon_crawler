"""
Console UI implementation.
Handles user input/output for the text-based game interface.
"""

import os
from typing import Optional, List
from colorama import init, Fore, Back, Style

from src.core.interfaces import IObserver
from src.core.event_system import EventSystem, GameEvents


class ConsoleUI(IObserver):
    """
    Console-based user interface.
    Adapter pattern - adapts game events to console output.

    GRASP Patterns:
    - Pure Fabrication: UI doesn't represent domain concept
    - Low Coupling: UI is decoupled from game logic
    """

    def __init__(self):
        """Initialize console UI."""
        # Initialize colorama for cross-platform colored output
        init(autoreset=True)

        self.event_system = EventSystem()
        self.message_buffer: List[str] = []
        self.input_prompt = "> "

        # Color scheme
        self.colors = {
            "info": Fore.WHITE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "combat": Fore.RED + Style.BRIGHT,
            "exploration": Fore.CYAN,
            "inventory": Fore.BLUE,
            "system": Fore.MAGENTA,
            "menu": Fore.WHITE + Style.BRIGHT,
            "game_over": Fore.RED + Back.BLACK + Style.BRIGHT,
            "victory": Fore.GREEN + Back.BLACK + Style.BRIGHT,
            "achievement": Fore.YELLOW + Style.BRIGHT,
            "boss_spawn": Fore.RED + Style.BRIGHT,
            "discovery": Fore.CYAN + Style.BRIGHT
        }

        # Subscribe to UI events
        self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant game events."""
        self.event_system.attach(self, GameEvents.UI_MESSAGE)
        self.event_system.attach(self, GameEvents.UI_ERROR)
        self.event_system.attach(self, GameEvents.UI_WARNING)

    def update(self, event: str, data: dict) -> None:
        """
        Handle game events (Observer pattern).

        Args:
            event: Event name
            data: Event data
        """
        message = data.get("message", "")
        msg_type = data.get("type", "info")

        if message:
            self.display_message(message, msg_type)

    def display_message(self, message: str, msg_type: str = "info") -> None:
        """
        Display message with appropriate formatting.

        Args:
            message: Message to display
            msg_type: Message type for color coding
        """
        color = self.colors.get(msg_type, Fore.WHITE)

        # Add special formatting for certain message types
        if msg_type == "combat":
            message = f"⚔️  {message}"
        elif msg_type == "warning":
            message = f"⚠️  {message}"
        elif msg_type == "error":
            message = f"❌ {message}"
        elif msg_type == "success":
            message = f"✅ {message}"
        elif msg_type == "achievement":
            message = f"\n{'='*40}\n{message}\n{'='*40}"
        elif msg_type == "discovery":
            message = f"🗺️  {message}"

        print(f"{color}{message}{Style.RESET_ALL}")

    def get_input(self, prompt: Optional[str] = None) -> str:
        """
        Get user input.

        Args:
            prompt: Optional custom prompt

        Returns:
            User input string
        """
        prompt = prompt or self.input_prompt
        try:
            return input(f"{Fore.WHITE}{prompt}{Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            print("\n\nGame interrupted. Type 'quit' to exit properly.")
            return "quit"

    def clear_screen(self) -> None:
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_banner(self) -> None:
        """Display game banner."""
        banner = f"""{Fore.CYAN + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         ██████╗ ██╗   ██╗███╗   ██╗ ██████╗                 ║
║         ██╔══██╗██║   ██║████╗  ██║██╔════╝                 ║
║         ██║  ██║██║   ██║██╔██╗ ██║██║  ███╗                ║
║         ██║  ██║██║   ██║██║╚██╗██║██║   ██║                ║
║         ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝                ║
║         ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝                 ║
║                                                              ║
║              ██████╗██████╗  █████╗ ██╗    ██╗              ║
║             ██╔════╝██╔══██╗██╔══██╗██║    ██║              ║
║             ██║     ██████╔╝███████║██║ █╗ ██║              ║
║             ██║     ██╔══██╗██╔══██║██║███╗██║              ║
║             ╚██████╗██║  ██║██║  ██║╚███╔███╔╝              ║
║              ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝               ║
║                                                              ║
║                    Design Patterns Demo                      ║
║                         Version 1.0                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
        print(banner)

    def display_help(self) -> None:
        """Display help information."""
        help_text = f"""{Fore.YELLOW}
═══════════════════════════════════════════════════════════════
                         GAME COMMANDS
═══════════════════════════════════════════════════════════════

{Fore.CYAN}MOVEMENT:{Style.RESET_ALL}
  move <direction>  - Move to another room
                     (north/n, south/s, east/e, west/w)

{Fore.RED}COMBAT:{Style.RESET_ALL}
  attack [target]   - Attack an enemy
  defend           - Take defensive stance (-50% damage taken)
  flee             - Attempt to escape from combat

{Fore.BLUE}ITEMS:{Style.RESET_ALL}
  take <item>      - Pick up an item from the room
  use <item>       - Use an item from your inventory
  equip <item>     - Equip a weapon or armor
  inventory (i)    - Display your inventory

{Fore.GREEN}INFORMATION:{Style.RESET_ALL}
  look (l)         - Examine the current room
  stats            - View your character statistics
  help             - Display this help message

{Fore.MAGENTA}SYSTEM:{Style.RESET_ALL}
  save             - Save your game
  load             - Load a saved game
  quit             - Return to main menu

{Fore.YELLOW}TIPS:{Style.RESET_ALL}
  • Explore carefully - some rooms contain traps!
  • Manage your health with potions
  • Better weapons can be found deeper in the dungeon
  • Some doors are locked and require keys
  • The exit is guarded by a powerful boss
═══════════════════════════════════════════════════════════════
{Style.RESET_ALL}"""
        print(help_text)

    def display_separator(self, char: str = "─", length: int = 60) -> None:
        """
        Display a separator line.

        Args:
            char: Character to use for separator
            length: Length of separator
        """
        print(f"{Fore.WHITE}{char * length}{Style.RESET_ALL}")

    def display_room_map(self, rooms_visited: List[str], current_room: str) -> None:
        """
        Display simple ASCII map of visited rooms.

        Args:
            rooms_visited: List of visited room names
            current_room: Current room name
        """
        # Simplified map display
        map_str = f"{Fore.CYAN}MAP:{Style.RESET_ALL}\n"
        for room in rooms_visited:
            if room == current_room:
                map_str += f"  {Fore.GREEN}[{room}] <-- You are here{Style.RESET_ALL}\n"
            else:
                map_str += f"  {Fore.WHITE}{room}{Style.RESET_ALL}\n"

        print(map_str)

    def format_statistics(self, stats: dict) -> str:
        """
        Format game statistics for display.

        Args:
            stats: Statistics dictionary

        Returns:
            Formatted statistics string
        """
        stats_str = f"{Fore.YELLOW}{'='*40}\n"
        stats_str += "         GAME STATISTICS\n"
        stats_str += f"{'='*40}{Style.RESET_ALL}\n"

        for key, value in stats.items():
            key_formatted = key.replace("_", " ").title()
            stats_str += f"{Fore.CYAN}{key_formatted:.<25}{Fore.WHITE}{value:>10}{Style.RESET_ALL}\n"

        stats_str += f"{Fore.YELLOW}{'='*40}{Style.RESET_ALL}"

        return stats_str

    def prompt_choice(self, question: str, choices: List[str]) -> str:
        """
        Prompt user to make a choice.

        Args:
            question: Question to ask
            choices: List of valid choices

        Returns:
            User's choice
        """
        print(f"\n{Fore.YELLOW}{question}{Style.RESET_ALL}")

        for i, choice in enumerate(choices, 1):
            print(f"  {Fore.CYAN}{i}.{Style.RESET_ALL} {choice}")

        while True:
            response = self.get_input("Choice: ")

            # Check if numeric choice
            if response.isdigit():
                index = int(response) - 1
                if 0 <= index < len(choices):
                    return choices[index]

            # Check if text choice
            response_lower = response.lower()
            for choice in choices:
                if choice.lower().startswith(response_lower):
                    return choice

            self.display_message("Invalid choice. Please try again.", "error")

    def confirm_action(self, message: str) -> bool:
        """
        Ask for confirmation.

        Args:
            message: Confirmation message

        Returns:
            True if confirmed
        """
        response = self.get_input(f"{message} (y/n): ").lower()
        return response in ['y', 'yes']


class ConsoleAdapter:
    """
    Adapter pattern - adapts ConsoleUI to different output formats.
    Could be extended for different UI backends (GUI, web, etc.)
    """

    def __init__(self, console_ui: ConsoleUI):
        """
        Initialize adapter.

        Args:
            console_ui: Console UI instance
        """
        self.console_ui = console_ui

    def output(self, message: str, msg_type: str = "info") -> None:
        """
        Output message through adapted interface.

        Args:
            message: Message to output
            msg_type: Message type
        """
        self.console_ui.display_message(message, msg_type)

    def input(self, prompt: str = "") -> str:
        """
        Get input through adapted interface.

        Args:
            prompt: Input prompt

        Returns:
            User input
        """
        return self.console_ui.get_input(prompt)

    def clear(self) -> None:
        """Clear display."""
        self.console_ui.clear_screen()


# ============= Singleton Instance =============

_console_ui_instance: Optional[ConsoleUI] = None


def get_console_ui() -> ConsoleUI:
    """
    Get singleton instance of console UI.

    Returns:
        Console UI instance
    """
    global _console_ui_instance
    if _console_ui_instance is None:
        _console_ui_instance = ConsoleUI()
    return _console_ui_instance
