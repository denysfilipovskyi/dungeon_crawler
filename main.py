"""
Main entry point for Dungeon Crawler game.
Demonstrates various design patterns in a cohesive project.
"""

from src.ui.console_ui import get_console_ui
from src.core.game_engine import get_game_engine
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Game:
    """
    Main game class.
    Coordinates game engine and UI.
    """

    def __init__(self):
        """Initialize game."""
        self.engine = get_game_engine()
        self.ui = get_console_ui()
        self.running = False

    def run(self) -> None:
        """Main game loop."""
        try:
            # Display banner
            self.ui.clear_screen()
            self.ui.display_banner()

            # Start engine
            self.engine.start()
            self.running = True

            # Game loop
            while self.running and self.engine.is_running():
                # Get and process input
                user_input = self.ui.get_input()

                if user_input.lower() in ['exit', 'quit'] and self.ui.confirm_action("Are you sure you want to quit?"):
                    break

                # Handle input through engine
                self.engine.handle_input(user_input)

                # Update game state
                self.engine.update()

            # Clean shutdown
            self.shutdown()

        except KeyboardInterrupt:
            print("\n\nGame interrupted.")
            self.shutdown()
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            import traceback
            traceback.print_exc()
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown game cleanly."""
        if self.engine:
            self.engine.stop()

        self.ui.display_separator()
        self.ui.display_message(
            "Thank you for playing Dungeon Crawler!", "success")
        self.ui.display_message(
            "A Design Patterns demonstration project.", "info")
        self.running = False


def main():
    """Main function."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
