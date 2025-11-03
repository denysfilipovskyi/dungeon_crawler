"""
Main Game Engine implementation using Facade pattern.
Provides a simplified interface to the complex game subsystems.
"""

from typing import Optional, Dict, Any

from src.core.interfaces import EntityType, ItemType, IState, IMemento
from src.core.event_system import EventSystem, GameEvents, AchievementObserver, LoggingObserver
from src.core.game_state import MenuState, SaveGameManager, GameMemento
from src.entities.factories import get_entity_factory
from src.items.inventory import Inventory, get_item_factory
from src.dungeon.builders import DungeonDirector
from src.dungeon.room import Room, Dungeon
from src.entities.base import Entity


class GameEngine:
    """
    Main game engine - Facade pattern.
    Provides simplified interface to all game subsystems.

    Design Patterns:
    - Facade: Simplifies complex subsystem interactions
    - Mediator: Coordinates between different game components
    - Singleton: Only one game engine instance

    GRASP Patterns:
    - Controller: Main game controller
    - Information Expert: Knows about overall game state
    - Low Coupling: Subsystems don't know about each other
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize game engine."""
        if not self._initialized:
            # Core systems
            self.event_system = EventSystem()
            self.save_manager = SaveGameManager()

            # Factories
            self.entity_factory = get_entity_factory()
            self.item_factory = get_item_factory()
            self.dungeon_director = DungeonDirector()

            # Game state
            self.current_state: Optional[IState] = None
            self.running = False

            # Game objects
            self.player: Optional[Entity] = None
            self.player_inventory: Optional[Inventory] = None
            self.dungeon: Optional[Dungeon] = None
            self.current_room: Optional[Room] = None

            # Statistics
            self.game_statistics = {
                "rooms_explored": 0,
                "enemies_defeated": 0,
                "items_collected": 0,
                "damage_dealt": 0,
                "damage_taken": 0,
                "potions_used": 0,
                "game_time": 0
            }

            # Initialize observers
            self._setup_observers()

            self._initialized = True

    def _setup_observers(self) -> None:
        """Set up event observers."""
        # Achievement tracking
        achievement_observer = AchievementObserver()
        self.event_system.attach(achievement_observer)

        # Logging
        log_observer = LoggingObserver("game_log.txt")
        self.event_system.attach(log_observer)

        # Statistics tracking
        self.event_system.attach(self, GameEvents.ROOM_ENTERED)
        self.event_system.attach(self, GameEvents.ENTITY_DIED)
        self.event_system.attach(self, GameEvents.ITEM_PICKED_UP)

    # ============= Game Flow Methods =============

    def start(self) -> None:
        """Start the game engine."""
        self.running = True

        # Set initial state
        self.change_state(MenuState(self))

        # Notify game start
        self.event_system.notify(GameEvents.GAME_STARTED, {
            "engine": self
        })

    def stop(self) -> None:
        """Stop the game engine."""
        self.running = False

        # Notify game end
        self.event_system.notify(GameEvents.GAME_OVER, {
            "statistics": self.game_statistics
        })

    def handle_input(self, input_str: str) -> None:
        """
        Handle player input.

        Args:
            input_str: Player input string
        """
        if not self.current_state:
            return

        # Parse input
        parts = input_str.strip().split(maxsplit=1)
        if not parts:
            return

        command = parts[0]
        args = parts[1].split() if len(parts) > 1 else []

        # Let current state handle input
        new_state = self.current_state.handle_input(command, args)

        if new_state:
            self.change_state(new_state)

    def change_state(self, new_state: IState) -> None:
        """
        Change game state.

        Args:
            new_state: New state to transition to
        """
        if self.current_state:
            self.current_state.exit()

        self.current_state = new_state
        self.current_state.enter()

    # ============= Game Initialization =============

    def start_new_game(self, difficulty: str = "normal") -> None:
        """
        Start a new game.

        Args:
            difficulty: Game difficulty (easy, normal, hard)
        """
        # Create player
        self._create_player()

        # Create dungeon based on difficulty
        self._create_dungeon(difficulty)

        # Initialize inventory
        self.player_inventory = Inventory("Player Inventory", capacity=20)

        # Give starting items
        self._give_starting_items()

        # Place player in entrance
        if self.dungeon and self.dungeon.entrance:
            self.current_room = self.dungeon.entrance
            self.current_room.enter(self.player)

        # Reset statistics
        self._reset_statistics()

        # Notify new game
        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": "New game started! Good luck, adventurer!",
            "type": "system"
        })

    def _create_player(self) -> None:
        """Create player character."""
        self.player = self.entity_factory.create(
            entity_type=EntityType.PLAYER,
            name="Hero"
        )

    def _create_dungeon(self, difficulty: str) -> None:
        """
        Create dungeon based on difficulty.

        Args:
            difficulty: Difficulty level
        """
        if difficulty == "easy":
            self.dungeon = self.dungeon_director.construct_beginner_dungeon()
        elif difficulty == "hard":
            self.dungeon = self.dungeon_director.construct_advanced_dungeon()
        else:  # normal
            self.dungeon = self.dungeon_director.construct_intermediate_dungeon()

    def _give_starting_items(self) -> None:
        """Give player starting items."""
        # Starting weapon
        sword = self.item_factory.create(ItemType.SWORD, level=1)
        self.player_inventory.add(sword)

        # Starting potions
        for _ in range(3):
            potion = self.item_factory.create(ItemType.POTION, level=1)
            self.player_inventory.add(potion)

    def _reset_statistics(self) -> None:
        """Reset game statistics."""
        self.game_statistics = {
            "rooms_explored": 0,
            "enemies_defeated": 0,
            "items_collected": 0,
            "damage_dealt": 0,
            "damage_taken": 0,
            "potions_used": 0,
            "game_time": 0
        }

    # ============= Save/Load System (Memento pattern) =============

    def save_game(self, filename: str = "savegame.json") -> bool:
        """
        Save current game state.

        Args:
            filename: Save file name

        Returns:
            True if saved successfully
        """
        try:
            # Create memento
            memento = self.create_memento()

            # Save to file
            success = self.save_manager.save_game(memento, filename)

            if success:
                self.event_system.notify(GameEvents.GAME_SAVED, {
                    "filename": filename
                })

            return success
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, filename: str = "savegame.json") -> bool:
        """
        Load game from save file.

        Args:
            filename: Save file name

        Returns:
            True if loaded successfully
        """
        try:
            # Load memento
            memento = self.save_manager.load_game(filename)

            if not memento:
                return False

            # Restore from memento
            self.restore_from_memento(memento)

            self.event_system.notify(GameEvents.GAME_LOADED, {
                "filename": filename
            })

            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False

    def create_memento(self) -> IMemento:
        """
        Create memento with current game state.

        Returns:
            Game memento
        """
        state = {
            "player": self._serialize_player() if self.player else None,
            "inventory": self._serialize_inventory() if self.player_inventory else None,
            "dungeon": self._serialize_dungeon() if self.dungeon else None,
            "current_room": self.current_room.name if self.current_room else None,
            "statistics": self.game_statistics.copy()
        }

        return GameMemento(state)

    def restore_from_memento(self, memento: IMemento) -> None:
        """
        Restore game state from memento.

        Args:
            memento: Game memento
        """
        state = memento.get_state()

        # Restore player
        if state.get("player"):
            self._restore_player(state["player"])

        # Restore inventory
        if state.get("inventory"):
            self._restore_inventory(state["inventory"])

        # Restore dungeon
        if state.get("dungeon"):
            self._restore_dungeon(state["dungeon"])

        # Restore current room
        if state.get("current_room") and self.dungeon:
            self.current_room = self.dungeon.find_room(state["current_room"])

        # Restore statistics
        if state.get("statistics"):
            self.game_statistics = state["statistics"]

    def _serialize_player(self) -> Dict[str, Any]:
        """Serialize player state."""
        return {
            "name": self.player.name,
            "stats": {
                "health": self.player.stats.health,
                "max_health": self.player.stats.max_health,
                "attack": self.player.stats.attack,
                "defense": self.player.stats.defense
            },
            "status_effects": self.player.status_effects.copy()
        }

    def _restore_player(self, data: Dict[str, Any]) -> None:
        """Restore player from serialized data."""
        self.player = self.entity_factory.create(
            entity_type=EntityType.PLAYER,
            name=data["name"]
        )

        # Restore stats
        stats = data["stats"]
        self.player.stats.health = stats["health"]
        self.player.stats.max_health = stats["max_health"]
        self.player.stats.attack = stats["attack"]
        self.player.stats.defense = stats["defense"]

        # Restore status effects
        self.player.status_effects = data.get("status_effects", {})

    def _serialize_inventory(self) -> Dict[str, Any]:
        """Serialize inventory state."""
        items = []
        for item in self.player_inventory.get_children():
            items.append({
                "name": item.name,
                "type": item.item_type.value if hasattr(item, 'item_type') else "unknown",
                "equipped": item.equipped if hasattr(item, 'equipped') else False
            })

        return {
            "capacity": self.player_inventory.capacity,
            "items": items
        }

    def _restore_inventory(self, data: Dict[str, Any]) -> None:
        """Restore inventory from serialized data."""
        self.player_inventory = Inventory(
            "Player Inventory", capacity=data["capacity"])

        # Note: Simplified restoration - in full implementation would restore exact items
        # For now, just create new items based on saved data

    def _serialize_dungeon(self) -> Dict[str, Any]:
        """Serialize dungeon state."""
        rooms = []
        for room in self.dungeon.rooms:
            rooms.append({
                "name": room.name,
                "visited": room.visited,
                "cleared": room.cleared,
                "position": {"x": room.position.x, "y": room.position.y}
            })

        return {
            "name": self.dungeon.name,
            "rooms": rooms
        }

    def _restore_dungeon(self, data: Dict[str, Any]) -> None:
        """Restore dungeon from serialized data."""
        # Note: Simplified restoration
        # In full implementation, would rebuild exact dungeon layout
        self._create_dungeon("normal")

        # Restore room states
        for room_data in data.get("rooms", []):
            room = self.dungeon.find_room(room_data["name"])
            if room:
                room.visited = room_data["visited"]
                room.cleared = room_data["cleared"]

    # ============= Statistics and Info =============

    def get_game_statistics(self) -> Dict[str, Any]:
        """
        Get current game statistics.

        Returns:
            Game statistics
        """
        return self.game_statistics.copy()

    def update_statistic(self, stat_name: str, value: Any) -> None:
        """
        Update game statistic.

        Args:
            stat_name: Statistic name
            value: New value or increment
        """
        if stat_name in self.game_statistics:
            if isinstance(self.game_statistics[stat_name], int):
                self.game_statistics[stat_name] += value
            else:
                self.game_statistics[stat_name] = value

    # ============= Event Observer Implementation =============

    def update(self, event: str, data: Dict[str, Any]) -> None:
        """
        Handle observed events.

        Args:
            event: Event name
            data: Event data
        """
        if event == GameEvents.ROOM_ENTERED:
            self.update_statistic("rooms_explored", 1)
        elif event == GameEvents.ENTITY_DIED:
            if data.get("entity") != self.player:
                self.update_statistic("enemies_defeated", 1)
        elif event == GameEvents.ITEM_PICKED_UP:
            self.update_statistic("items_collected", 1)

    # ============= Utility Methods =============

    def quit_game(self) -> None:
        """Quit the game."""
        self.stop()

    def is_running(self) -> bool:
        """Check if game is running."""
        return self.running

    def get_current_state_type(self) -> Optional[str]:
        """Get current state type."""
        if self.current_state:
            return self.current_state.state_type.value
        return None


# ============= Singleton Instance =============

def get_game_engine() -> GameEngine:
    """
    Get singleton instance of game engine.

    Returns:
        Game engine instance
    """
    return GameEngine()
