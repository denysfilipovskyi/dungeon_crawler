"""
Event System implementation using Observer pattern.
This is a Pure Fabrication (GRASP) - a class that doesn't represent a domain concept
but improves design by achieving Low Coupling and High Cohesion.
"""

from typing import Dict, List, Any, Optional
from src.core.interfaces import IObserver, IObservable
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EventSystem(IObservable):
    """
    Singleton Event System implementing Observer pattern.
    Manages all game events and notifications.

    Design Patterns used:
    - Singleton: Only one event system exists
    - Observer: Notifies subscribers about events
    """

    _instance: Optional['EventSystem'] = None

    def __new__(cls) -> 'EventSystem':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize event system if not already initialized."""
        if not self._initialized:
            self._observers: Dict[str, List[IObserver]] = {}
            self._event_history: List[Dict[str, Any]] = []
            self._initialized = True
            logger.info("EventSystem initialized")

    def attach(self, observer: IObserver, event_type: str = None) -> None:
        """
        Attach observer to specific event type or all events.

        Args:
            observer: Observer to attach
            event_type: Specific event to subscribe to, or None for all events
        """
        event_key = event_type or "*"  # "*" means subscribe to all events

        if event_key not in self._observers:
            self._observers[event_key] = []

        if observer not in self._observers[event_key]:
            self._observers[event_key].append(observer)
            logger.debug(
                f"Observer {observer.__class__.__name__} attached to event '{event_key}'")

    def detach(self, observer: IObserver, event_type: str = None) -> None:
        """
        Detach observer from specific event type or all events.

        Args:
            observer: Observer to detach
            event_type: Specific event to unsubscribe from, or None for all events
        """
        event_key = event_type or "*"

        if event_key in self._observers and observer in self._observers[event_key]:
            self._observers[event_key].remove(observer)
            logger.debug(
                f"Observer {observer.__class__.__name__} detached from event '{event_key}'")

    def notify(self, event: str, data: Dict[str, Any] = None) -> None:
        """
        Notify all observers about an event.

        Args:
            event: Event name
            data: Event data
        """
        data = data or {}

        # Record event in history
        self._event_history.append({
            'event': event,
            'data': data,
            'timestamp': self._get_timestamp()
        })

        # Notify specific event observers
        if event in self._observers:
            for observer in self._observers[event]:
                try:
                    observer.update(event, data)
                except Exception as e:
                    logger.error(
                        f"Error notifying observer {observer.__class__.__name__}: {e}")

        # Notify universal observers (subscribed to all events)
        if "*" in self._observers:
            for observer in self._observers["*"]:
                try:
                    observer.update(event, data)
                except Exception as e:
                    logger.error(
                        f"Error notifying universal observer {observer.__class__.__name__}: {e}")

        logger.info(f"Event '{event}' triggered with data: {data}")

    def get_event_history(self, event_type: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get event history, optionally filtered by event type.

        Args:
            event_type: Filter by specific event type
            limit: Maximum number of events to return

        Returns:
            List of event records
        """
        history = self._event_history

        if event_type:
            history = [e for e in history if e['event'] == event_type]

        if limit:
            history = history[-limit:]

        return history

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")

    def reset(self) -> None:
        """Reset event system (mainly for testing)."""
        self._observers.clear()
        self._event_history.clear()
        logger.info("EventSystem reset")

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# ============= Event Types =============

class GameEvents:
    """
    Constants for game events.
    This serves as a catalog of all possible events in the game.
    """

    # Game flow events
    GAME_STARTED = "game_started"
    GAME_OVER = "game_over"
    GAME_WON = "game_won"
    GAME_SAVED = "game_saved"
    GAME_LOADED = "game_loaded"

    # Player events
    PLAYER_MOVED = "player_moved"
    PLAYER_ATTACKED = "player_attacked"
    PLAYER_DEFENDED = "player_defended"
    PLAYER_DAMAGED = "player_damaged"
    PLAYER_HEALED = "player_healed"
    PLAYER_DIED = "player_died"
    PLAYER_LEVELED_UP = "player_leveled_up"

    # Entity events
    ENTITY_SPAWNED = "entity_spawned"
    ENTITY_DIED = "entity_died"
    ENTITY_DAMAGED = "entity_damaged"

    # Item events
    ITEM_PICKED_UP = "item_picked_up"
    ITEM_DROPPED = "item_dropped"
    ITEM_USED = "item_used"
    ITEM_EQUIPPED = "item_equipped"
    ITEM_UNEQUIPPED = "item_unequipped"

    # Room events
    ROOM_ENTERED = "room_entered"
    ROOM_EXITED = "room_exited"
    ROOM_CLEARED = "room_cleared"

    # Combat events
    COMBAT_STARTED = "combat_started"
    COMBAT_ENDED = "combat_ended"
    COMBAT_TURN = "combat_turn"

    # UI events
    UI_MESSAGE = "ui_message"
    UI_ERROR = "ui_error"
    UI_WARNING = "ui_warning"


# ============= Event Listeners (Observers) =============

class LoggingObserver(IObserver):
    """
    Observer that logs all events to a file.
    Example of Observer pattern implementation.
    """

    def __init__(self, log_file: str = "game_events.log"):
        """Initialize logging observer."""
        self.log_file = log_file
        self.file_logger = logging.getLogger(f"{__name__}.FileLogger")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.file_logger.addHandler(handler)
        self.file_logger.setLevel(logging.INFO)

    def update(self, event: str, data: Dict[str, Any]) -> None:
        """Log event to file."""
        self.file_logger.info(f"Event: {event} | Data: {data}")


class AchievementObserver(IObserver):
    """
    Observer that tracks achievements.
    Example of how Observer pattern enables extensibility.
    """

    def __init__(self):
        """Initialize achievement tracker."""
        self.achievements = {
            "first_kill": False,
            "dragon_slayer": False,
            "treasure_hunter": False,
            "survivor": False,
            "speedrunner": False
        }
        self.kill_count = 0
        self.items_collected = 0
        self.rooms_explored = 0

    def update(self, event: str, data: Dict[str, Any]) -> None:
        """Check for achievement conditions."""
        if event == GameEvents.ENTITY_DIED:
            self.kill_count += 1
            if self.kill_count == 1:
                self._unlock_achievement("first_kill", "First Blood")

            if data.get("entity_type") == "dragon":
                self._unlock_achievement("dragon_slayer", "Dragon Slayer")

        elif event == GameEvents.ITEM_PICKED_UP:
            self.items_collected += 1
            if self.items_collected >= 10:
                self._unlock_achievement("treasure_hunter", "Treasure Hunter")

        elif event == GameEvents.ROOM_ENTERED:
            self.rooms_explored += 1
            if self.rooms_explored >= 20:
                self._unlock_achievement("survivor", "Dungeon Explorer")

    def _unlock_achievement(self, key: str, name: str) -> None:
        """Unlock an achievement."""
        if not self.achievements[key]:
            self.achievements[key] = True
            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": f"🏆 Achievement Unlocked: {name}!",
                "type": "achievement"
            })
