"""
Game state management using State pattern.
Manages different game states and transitions.
"""

from typing import Optional, Dict, Any, List
from abc import abstractmethod
import json
import os
from datetime import datetime

from src.core.interfaces import IState, GameStateType, IMemento
from src.core.event_system import EventSystem, GameEvents
from src.ui.commands import CommandProcessor
from src.combat.combat_system import get_combat_system


class GameState(IState):
    """
    Base game state implementation.
    State pattern for game flow management.
    """

    def __init__(self, game_engine: Any):
        """
        Initialize game state.

        Args:
            game_engine: Reference to game engine
        """
        self.game_engine = game_engine
        self.event_system = EventSystem()
        self.state_type = GameStateType.MENU

    @abstractmethod
    def enter(self) -> None:
        """Called when entering this state."""
        pass

    @abstractmethod
    def exit(self) -> None:
        """Called when exiting this state."""
        pass

    @abstractmethod
    def handle_input(self, command: str, args: List[str]) -> Optional['IState']:
        """
        Handle player input.

        Args:
            command: Command string
            args: Command arguments

        Returns:
            New state if transition needed
        """
        pass

    @abstractmethod
    def update(self) -> Optional['IState']:
        """
        Update state.

        Returns:
            New state if transition needed
        """
        pass

    def _show_message(self, message: str, msg_type: str = "info") -> None:
        """
        Show message to player.

        Args:
            message: Message to show
            msg_type: Message type
        """
        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": message,
            "type": msg_type
        })


# ============= Concrete States =============

class MenuState(GameState):
    """Main menu state."""

    def __init__(self, game_engine: Any):
        """Initialize menu state."""
        super().__init__(game_engine)
        self.state_type = GameStateType.MENU

    def enter(self) -> None:
        """Show main menu."""
        menu_text = """
╔══════════════════════════════════════╗
║      DUNGEON CRAWLER ADVENTURE      ║
║           Design Patterns Demo       ║
╚══════════════════════════════════════╝

Commands:
  new    - Start new game
  load   - Load saved game
  help   - Show help
  quit   - Exit game

Enter command: """
        self._show_message(menu_text, "menu")

    def exit(self) -> None:
        """Exit menu state."""
        pass

    def handle_input(self, command: str, args: List[str]) -> Optional[IState]:
        """Handle menu input."""
        command = command.lower()

        if command == "new":
            # Start new game
            self.game_engine.start_new_game()
            return ExploringState(self.game_engine)

        elif command == "load":
            # Load saved game
            if self.game_engine.load_game():
                self._show_message("Game loaded successfully!", "success")
                return ExploringState(self.game_engine)
            else:
                self._show_message("No saved game found.", "error")

        elif command == "help":
            self._show_help()

        elif command == "quit":
            return GameOverState(self.game_engine, victory=False)

        else:
            self._show_message(f"Unknown menu command: {command}", "error")

        return None

    def update(self) -> Optional[IState]:
        """Update menu state."""
        return None

    def _show_help(self) -> None:
        """Show help text."""
        help_text = """
GAME CONTROLS:
============
Movement:
  move <direction> - Move (north/south/east/west or n/s/e/w)

Combat:
  attack [target]  - Attack enemy
  defend          - Take defensive stance
  flee            - Try to escape combat

Items:
  take <item>     - Pick up item
  use <item>      - Use item from inventory
  equip <item>    - Equip weapon/armor
  inventory (i)   - Show inventory

Information:
  look (l)        - Examine current room
  stats           - Show player stats
  help            - Show this help

System:
  save            - Save game
  load            - Load game
  quit            - Exit to menu
"""
        self._show_message(help_text, "help")


class ExploringState(GameState):
    """Exploration state - main gameplay."""

    def __init__(self, game_engine: Any):
        """Initialize exploring state."""
        super().__init__(game_engine)
        self.state_type = GameStateType.EXPLORING
        self.command_processor = CommandProcessor()

    def enter(self) -> None:
        """Enter exploration mode."""
        self._show_message("\n=== Exploration Mode ===", "state")

        # Show current room
        if self.game_engine.current_room:
            self._show_message(
                self.game_engine.current_room.get_description(), "exploration")

        # Check for immediate combat
        if self.game_engine.current_room and self.game_engine.current_room.has_hostile_entities():
            self._show_message(
                "\n⚠️ Enemies detected! Prepare for combat!", "warning")

    def exit(self) -> None:
        """Exit exploration state."""
        pass

    def handle_input(self, command: str, args: List[str]) -> Optional[IState]:
        """Handle exploration input."""
        # Check for state-changing commands
        if command.lower() == "quit":
            return MenuState(self.game_engine)

        elif command.lower() == "save":
            if self.game_engine.save_game():
                self._show_message("Game saved successfully!", "success")
            else:
                self._show_message("Failed to save game.", "error")
            return None

        elif command.lower() == "help":
            MenuState(self.game_engine)._show_help()
            return None

        # Build full command string
        full_command = f"{command} {' '.join(args)}" if args else command

        # Process through command system
        game_context = {
            "player": self.game_engine.player,
            "current_room": self.game_engine.current_room,
            "inventory": self.game_engine.player_inventory,
            "dungeon": self.game_engine.dungeon
        }

        self.command_processor.process_input(full_command, game_context)

        # Update current room reference
        self.game_engine.current_room = game_context.get("current_room")

        # Check for state changes after command
        return self._check_state_transitions()

    def update(self) -> Optional[IState]:
        """Update exploration state."""
        # Check for automatic state transitions
        return self._check_state_transitions()

    def _check_state_transitions(self) -> Optional[IState]:
        """Check if state transition is needed."""
        # Check for combat
        combat_system = get_combat_system()
        if combat_system.is_combat_active():
            return CombatState(self.game_engine)

        # Check for death
        if not self.game_engine.player.is_alive():
            return GameOverState(self.game_engine, victory=False)

        # Check for victory
        if self.game_engine.current_room and self.game_engine.current_room.is_exit:
            if not self.game_engine.current_room.has_hostile_entities():
                return VictoryState(self.game_engine)

        return None


class CombatState(GameState):
    """Combat state."""

    def __init__(self, game_engine: Any):
        """Initialize combat state."""
        super().__init__(game_engine)
        self.state_type = GameStateType.COMBAT
        self.command_processor = CommandProcessor()
        self.combat_system = get_combat_system()

    def enter(self) -> None:
        """Enter combat mode."""
        self._show_message("\n⚔️ === COMBAT MODE === ⚔️", "combat")
        self._show_message(
            "Commands: attack [target], defend, flee", "combat_info")

    def exit(self) -> None:
        """Exit combat state."""
        pass

    def handle_input(self, command: str, args: List[str]) -> Optional[IState]:
        """Handle combat input."""
        # Only combat commands allowed
        valid_commands = ["attack", "defend", "flee",
                          "run", "use", "stats", "inventory", "i"]

        if command.lower() not in valid_commands:
            self._show_message(
                "Invalid command during combat! Use: attack, defend, flee", "warning")
            return None

        # Process command
        full_command = f"{command} {' '.join(args)}" if args else command

        game_context = {
            "player": self.game_engine.player,
            "current_room": self.game_engine.current_room,
            "inventory": self.game_engine.player_inventory
        }

        self.command_processor.process_input(full_command, game_context)

        # Update current room (in case of flee)
        self.game_engine.current_room = game_context.get("current_room")

        # Check for state changes
        return self._check_combat_end()

    def update(self) -> Optional[IState]:
        """Update combat state."""
        return self._check_combat_end()

    def _check_combat_end(self) -> Optional[IState]:
        """Check if combat has ended."""
        if not self.combat_system.is_combat_active():
            # Combat ended
            if not self.game_engine.player.is_alive():
                return GameOverState(self.game_engine, victory=False)
            else:
                self._show_message(
                    "\nCombat ended. Returning to exploration.", "info")
                return ExploringState(self.game_engine)

        return None


class InventoryState(GameState):
    """Inventory management state."""

    def __init__(self, game_engine: Any):
        """Initialize inventory state."""
        super().__init__(game_engine)
        self.state_type = GameStateType.INVENTORY
        self.previous_state = None

    def enter(self) -> None:
        """Enter inventory mode."""
        self._show_message("\n=== Inventory Management ===", "inventory")
        self._show_message(str(self.game_engine.player_inventory), "inventory")
        self._show_message(
            "\nCommands: use <item>, equip <item>, drop <item>, back", "info")

    def exit(self) -> None:
        """Exit inventory state."""
        pass

    def handle_input(self, command: str, args: List[str]) -> Optional[IState]:
        """Handle inventory input."""
        if command.lower() == "back":
            # Return to previous state
            return self.previous_state or ExploringState(self.game_engine)

        # Handle inventory commands
        # ... inventory management logic ...

        return None

    def update(self) -> Optional[IState]:
        """Update inventory state."""
        return None


class GameOverState(GameState):
    """Game over state."""

    def __init__(self, game_engine: Any, victory: bool = False):
        """
        Initialize game over state.

        Args:
            game_engine: Game engine reference
            victory: Whether game ended in victory
        """
        super().__init__(game_engine)
        self.state_type = GameStateType.GAME_OVER if not victory else GameStateType.VICTORY
        self.victory = victory

    def enter(self) -> None:
        """Show game over screen."""
        if self.victory:
            self._show_victory_screen()
        else:
            self._show_game_over_screen()

    def exit(self) -> None:
        """Exit game over state."""
        pass

    def handle_input(self, command: str, args: List[str]) -> Optional[IState]:
        """Handle game over input."""
        if command.lower() in ["menu", "m", ""]:
            return MenuState(self.game_engine)
        elif command.lower() in ["quit", "q"]:
            self.game_engine.quit_game()
            return None
        else:
            self._show_message(
                "Press Enter to return to menu, or 'quit' to exit.", "info")

        return None

    def update(self) -> Optional[IState]:
        """Update game over state."""
        return None

    def _show_game_over_screen(self) -> None:
        """Show game over message."""
        message = """
╔══════════════════════════════════════╗
║             GAME OVER                ║
║         You have been defeated!      ║
╚══════════════════════════════════════╝

Press Enter to return to menu...
"""
        self._show_message(message, "game_over")

    def _show_victory_screen(self) -> None:
        """Show victory message."""
        stats = self.game_engine.get_game_statistics()
        message = f"""
╔══════════════════════════════════════╗
║             VICTORY!                 ║
║      You have escaped the dungeon!   ║
╚══════════════════════════════════════╝

Statistics:
  Rooms explored: {stats.get('rooms_explored', 0)}
  Enemies defeated: {stats.get('enemies_defeated', 0)}
  Items collected: {stats.get('items_collected', 0)}

Press Enter to return to menu...
"""
        self._show_message(message, "victory")


class VictoryState(GameOverState):
    """Victory state - special case of game over."""

    def __init__(self, game_engine: Any):
        """Initialize victory state."""
        super().__init__(game_engine, victory=True)


# ============= Save/Load System (Memento pattern) =============

class GameMemento(IMemento):
    """
    Memento for saving game state.
    Memento pattern implementation.
    """

    def __init__(self, state: Dict[str, Any]):
        """
        Initialize memento.

        Args:
            state: Game state to save
        """
        self._state = state
        self._timestamp = datetime.now().isoformat()

    def get_state(self) -> Dict[str, Any]:
        """Get saved state."""
        return self._state

    def get_timestamp(self) -> str:
        """Get save timestamp."""
        return self._timestamp


class SaveGameManager:
    """
    Manages game saving and loading.
    Caretaker in Memento pattern.
    """

    def __init__(self, save_dir: str = "saves"):
        """
        Initialize save manager.

        Args:
            save_dir: Directory for save files
        """
        self.save_dir = save_dir
        self._ensure_save_directory()

    def _ensure_save_directory(self) -> None:
        """Ensure save directory exists."""
        os.makedirs(self.save_dir, exist_ok=True)

    def save_game(self, memento: GameMemento, filename: str = "savegame.json") -> bool:
        """
        Save game to file.

        Args:
            memento: Game memento
            filename: Save file name

        Returns:
            True if saved successfully
        """
        try:
            filepath = os.path.join(self.save_dir, filename)

            save_data = {
                "timestamp": memento.get_timestamp(),
                "state": memento.get_state()
            }

            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, filename: str = "savegame.json") -> Optional[GameMemento]:
        """
        Load game from file.

        Args:
            filename: Save file name

        Returns:
            Game memento or None
        """
        try:
            filepath = os.path.join(self.save_dir, filename)

            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r') as f:
                save_data = json.load(f)

            return GameMemento(save_data["state"])
        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def list_saves(self) -> List[str]:
        """
        List available save files.

        Returns:
            List of save file names
        """
        try:
            files = os.listdir(self.save_dir)
            return [f for f in files if f.endswith('.json')]
        except Exception:
            return []

    def delete_save(self, filename: str) -> bool:
        """
        Delete save file.

        Args:
            filename: Save file to delete

        Returns:
            True if deleted successfully
        """
        try:
            filepath = os.path.join(self.save_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False
