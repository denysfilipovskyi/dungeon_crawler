"""
Command system implementation using Command pattern.
Handles player input and actions with undo capability.
"""

from typing import Optional, List, Dict, Any
from abc import abstractmethod
import copy

from src.core.interfaces import ICommand, IHandler, Direction
from src.core.event_system import EventSystem, GameEvents
from src.entities.base import Entity
from src.items.items import Item
from src.dungeon.room import Room
from src.combat.combat_system import get_combat_system


class Command(ICommand):
    """
    Base command implementation.
    Command pattern for encapsulating actions.
    """

    def __init__(self, game_context: Dict[str, Any]):
        """
        Initialize command.

        Args:
            game_context: Game state context
        """
        self.game_context = game_context
        self.player: Optional[Entity] = game_context.get("player")
        self.current_room: Optional[Room] = game_context.get("current_room")
        self.event_system = EventSystem()
        self.executed = False
        self.previous_state = None

    @abstractmethod
    def _execute_impl(self) -> bool:
        """Implementation-specific execution logic."""
        pass

    def execute(self) -> bool:
        """
        Execute command.

        Returns:
            True if successful
        """
        if not self.can_execute():
            return False

        # Save state for undo
        self.previous_state = self._save_state()

        # Execute command
        success = self._execute_impl()

        if success:
            self.executed = True

        return success

    def undo(self) -> None:
        """Undo command if possible."""
        if self.executed and self.previous_state:
            self._restore_state(self.previous_state)
            self.executed = False

    def can_execute(self) -> bool:
        """Check if command can be executed."""
        return self.player is not None and self.player.is_alive()

    def _save_state(self) -> Dict[str, Any]:
        """Save current state for undo."""
        return {
            "player_position": self.game_context.get("current_room"),
            "player_stats": copy.deepcopy(self.player.stats) if self.player else None
        }

    def _restore_state(self, state: Dict[str, Any]) -> None:
        """Restore saved state."""
        if "player_position" in state:
            self.game_context["current_room"] = state["player_position"]

        if "player_stats" in state and self.player:
            self.player.stats = state["player_stats"]


# ============= Movement Commands =============

class MoveCommand(Command):
    """Command for moving between rooms."""

    def __init__(self, game_context: Dict[str, Any], direction: Direction):
        """
        Initialize move command.

        Args:
            game_context: Game context
            direction: Direction to move
        """
        super().__init__(game_context)
        self.direction = direction

    def _execute_impl(self) -> bool:
        """Execute movement."""
        if not self.current_room:
            self.event_system.notify(GameEvents.UI_ERROR, {
                "message": "Cannot move - no current room!"
            })
            return False

        # Check if movement is possible
        connection = self.current_room.get_connection(self.direction)

        if not connection:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"There is no exit to the {self.direction.value}.",
                "type": "movement"
            })
            return False

        if connection.locked:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"The door to the {self.direction.value} is locked.",
                "type": "movement"
            })
            return False

        # Check for combat
        if self.current_room.has_hostile_entities():
            self.event_system.notify(GameEvents.UI_WARNING, {
                "message": "You cannot leave while enemies are present!",
                "type": "combat"
            })
            return False

        # Move to new room
        old_room = self.current_room
        new_room = connection.target_room

        old_room.exit(self.player)
        self.game_context["current_room"] = new_room
        self.current_room = new_room
        new_room.enter(self.player)

        self.event_system.notify(GameEvents.PLAYER_MOVED, {
            "from": old_room,
            "to": new_room,
            "direction": self.direction
        })

        return True

    def can_execute(self) -> bool:
        """Check if movement is possible."""
        if not super().can_execute():
            return False

        if not self.current_room:
            return False

        # Check if in combat
        combat_system = get_combat_system()
        if combat_system.is_combat_active():
            return False

        return True


# ============= Combat Commands =============

class AttackCommand(Command):
    """Command for attacking enemies."""

    def __init__(self, game_context: Dict[str, Any], target_name: Optional[str] = None):
        """
        Initialize attack command.

        Args:
            game_context: Game context
            target_name: Optional target name
        """
        super().__init__(game_context)
        self.target_name = target_name
        self.target: Optional[Entity] = None

    def _execute_impl(self) -> bool:
        """Execute attack."""
        if not self.current_room:
            return False

        # Find target
        living_entities = self.current_room.get_living_entities()
        hostile_entities = [e for e in living_entities if e != self.player]

        if not hostile_entities:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": "There is nothing to attack here.",
                "type": "combat"
            })
            return False

        # Select target
        if self.target_name:
            self.target = self._find_target_by_name(
                hostile_entities, self.target_name)
            if not self.target:
                self.event_system.notify(GameEvents.UI_MESSAGE, {
                    "message": f"Cannot find target: {self.target_name}",
                    "type": "combat"
                })
                return False
        else:
            # Attack first hostile entity
            self.target = hostile_entities[0]

        # Start combat if not active
        combat_system = get_combat_system()
        if not combat_system.is_combat_active():
            participants = [self.player] + hostile_entities
            combat_system.start_combat(participants)

        # Execute attack
        combat_system.execute_attack(self.player, self.target)

        # Continue combat
        combat_system.execute_round()

        return True

    def _find_target_by_name(self, entities: List[Entity], name: str) -> Optional[Entity]:
        """Find target entity by name."""
        name_lower = name.lower()
        for entity in entities:
            if entity.name.lower() == name_lower or name_lower in entity.name.lower():
                return entity
        return None


class DefendCommand(Command):
    """Command for taking defensive stance."""

    def _execute_impl(self) -> bool:
        """Execute defend action."""
        self.player.defend()

        self.event_system.notify(GameEvents.PLAYER_DEFENDED, {
            "player": self.player
        })

        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": "You take a defensive stance!",
            "type": "combat"
        })

        # Continue combat if active
        combat_system = get_combat_system()
        if combat_system.is_combat_active():
            combat_system.execute_round()

        return True


class FleeCommand(Command):
    """Command for fleeing from combat."""

    def _execute_impl(self) -> bool:
        """Execute flee action."""
        import random

        combat_system = get_combat_system()
        if not combat_system.is_combat_active():
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": "You are not in combat!",
                "type": "combat"
            })
            return False

        # Flee chance based on health
        health_percentage = self.player.stats.health / self.player.stats.max_health
        flee_chance = 0.3 + (health_percentage * 0.4)

        if random.random() < flee_chance:
            # Successful flee
            combat_system.end_combat()

            # Move to random adjacent room
            if self.current_room and self.current_room.connections:
                direction = random.choice(
                    list(self.current_room.connections.keys()))
                move_command = MoveCommand(self.game_context, direction)
                move_command.execute()

            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": "You successfully flee from combat!",
                "type": "combat"
            })
            return True
        else:
            # Failed flee - enemies get free attacks
            self.event_system.notify(GameEvents.UI_WARNING, {
                "message": "Failed to flee! Enemies attack!",
                "type": "combat"
            })
            combat_system.execute_round()
            return False


# ============= Item Commands =============

class TakeCommand(Command):
    """Command for picking up items."""

    def __init__(self, game_context: Dict[str, Any], item_name: str):
        """
        Initialize take command.

        Args:
            game_context: Game context
            item_name: Name of item to take
        """
        super().__init__(game_context)
        self.item_name = item_name

    def _execute_impl(self) -> bool:
        """Execute item pickup."""
        if not self.current_room:
            return False

        # Find item in room
        item = self._find_item(self.item_name)

        if not item:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"Cannot find item: {self.item_name}",
                "type": "inventory"
            })
            return False

        # Add to inventory
        inventory = self.game_context.get("inventory")
        if not inventory:
            self.event_system.notify(GameEvents.UI_ERROR, {
                "message": "No inventory available!",
                "type": "inventory"
            })
            return False

        if inventory.add(item):
            self.current_room.remove(item)

            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"You picked up: {item.name}",
                "type": "inventory"
            })
            return True
        else:
            self.event_system.notify(GameEvents.UI_WARNING, {
                "message": "Your inventory is full!",
                "type": "inventory"
            })
            return False

    def _find_item(self, name: str) -> Optional[Item]:
        """Find item by name in current room."""
        name_lower = name.lower()
        for item in self.current_room.items:
            if item.name.lower() == name_lower or name_lower in item.name.lower():
                return item
        return None


class UseCommand(Command):
    """Command for using items."""

    def __init__(self, game_context: Dict[str, Any], item_name: str):
        """
        Initialize use command.

        Args:
            game_context: Game context
            item_name: Name of item to use
        """
        super().__init__(game_context)
        self.item_name = item_name

    def _execute_impl(self) -> bool:
        """Execute item use."""
        inventory = self.game_context.get("inventory")
        if not inventory:
            return False

        # Find item in inventory
        item = inventory.find_item(self.item_name)

        if not item:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"You don't have: {self.item_name}",
                "type": "inventory"
            })
            return False

        # Use item
        if item.use(self.player):
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"You used: {item.name}",
                "type": "inventory"
            })

            # Remove consumables
            if hasattr(item, 'consumed') and item.consumed:
                inventory.remove(item)

            return True
        else:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"Cannot use {item.name} right now.",
                "type": "inventory"
            })
            return False


class EquipCommand(Command):
    """Command for equipping items."""

    def __init__(self, game_context: Dict[str, Any], item_name: str):
        """
        Initialize equip command.

        Args:
            game_context: Game context
            item_name: Name of item to equip
        """
        super().__init__(game_context)
        self.item_name = item_name

    def _execute_impl(self) -> bool:
        """Execute item equip."""
        inventory = self.game_context.get("inventory")
        if not inventory:
            return False

        # Find item
        item = inventory.find_item(self.item_name)

        if not item:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"You don't have: {self.item_name}",
                "type": "inventory"
            })
            return False

        # Equip item
        if inventory.equip_item(item, self.player):
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"You equipped: {item.name}",
                "type": "inventory"
            })
            return True
        else:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": f"Cannot equip {item.name}.",
                "type": "inventory"
            })
            return False


# ============= Information Commands =============

class LookCommand(Command):
    """Command for examining surroundings."""

    def _execute_impl(self) -> bool:
        """Execute look action."""
        if not self.current_room:
            return False

        description = self.current_room.get_description()

        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": f"\n{description}",
            "type": "exploration"
        })

        return True


class InventoryCommand(Command):
    """Command for viewing inventory."""

    def _execute_impl(self) -> bool:
        """Execute inventory view."""
        inventory = self.game_context.get("inventory")

        if not inventory:
            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": "You have no inventory!",
                "type": "inventory"
            })
            return False

        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": f"\n{inventory}",
            "type": "inventory"
        })

        # Show equipped items
        equipped = inventory.get_equipped_items()
        if equipped:
            equipped_str = "\nEquipped:\n"
            for item_type, item in equipped.items():
                equipped_str += f"  {item_type.value}: {item.name}\n"

            self.event_system.notify(GameEvents.UI_MESSAGE, {
                "message": equipped_str,
                "type": "inventory"
            })

        return True


class StatsCommand(Command):
    """Command for viewing player statistics."""

    def _execute_impl(self) -> bool:
        """Execute stats view."""
        if not self.player:
            return False

        stats_str = f"\n{self.player.name} Statistics:\n"
        stats_str += f"  Health: {self.player.stats.health}/{self.player.stats.max_health}\n"
        stats_str += f"  Attack: {self.player.stats.attack}\n"
        stats_str += f"  Defense: {self.player.stats.defense}\n"

        if self.player.status_effects:
            stats_str += f"  Effects: {', '.join(self.player.status_effects.keys())}\n"

        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": stats_str,
            "type": "player_info"
        })

        return True


# ============= Command Handler (Chain of Responsibility) =============

class CommandHandler(IHandler):
    """
    Base command handler for Chain of Responsibility pattern.
    """

    def __init__(self):
        """Initialize handler."""
        self._next_handler: Optional[IHandler] = None

    def set_next(self, handler: IHandler) -> IHandler:
        """
        Set next handler in chain.

        Args:
            handler: Next handler

        Returns:
            Handler for chaining
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any) -> Optional[Any]:
        """
        Handle request or pass to next handler.

        Args:
            request: Request to handle

        Returns:
            Result or None
        """
        if self._next_handler:
            return self._next_handler.handle(request)
        return None


class MovementHandler(CommandHandler):
    """Handler for movement commands."""

    def handle(self, request: Any) -> Optional[Any]:
        """Handle movement commands."""
        if isinstance(request, dict):
            command = request.get("command", "").lower()
            args = request.get("args", [])
            context = request.get("context", {})

            if command == "move" and args:
                direction_str = args[0].lower()

                # Parse direction
                direction_map = {
                    "north": Direction.NORTH,
                    "n": Direction.NORTH,
                    "south": Direction.SOUTH,
                    "s": Direction.SOUTH,
                    "east": Direction.EAST,
                    "e": Direction.EAST,
                    "west": Direction.WEST,
                    "w": Direction.WEST
                }

                if direction_str in direction_map:
                    direction = direction_map[direction_str]
                    return MoveCommand(context, direction)

        return super().handle(request)


class CombatHandler(CommandHandler):
    """Handler for combat commands."""

    def handle(self, request: Any) -> Optional[Any]:
        """Handle combat commands."""
        if isinstance(request, dict):
            command = request.get("command", "").lower()
            args = request.get("args", [])
            context = request.get("context", {})

            if command == "attack":
                target = args[0] if args else None
                return AttackCommand(context, target)
            elif command == "defend":
                return DefendCommand(context)
            elif command == "flee" or command == "run":
                return FleeCommand(context)

        return super().handle(request)


class ItemHandler(CommandHandler):
    """Handler for item commands."""

    def handle(self, request: Any) -> Optional[Any]:
        """Handle item commands."""
        if isinstance(request, dict):
            command = request.get("command", "").lower()
            args = request.get("args", [])
            context = request.get("context", {})

            if command == "take" and args:
                item_name = " ".join(args)
                return TakeCommand(context, item_name)
            elif command == "use" and args:
                item_name = " ".join(args)
                return UseCommand(context, item_name)
            elif command == "equip" and args:
                item_name = " ".join(args)
                return EquipCommand(context, item_name)

        return super().handle(request)


class InformationHandler(CommandHandler):
    """Handler for information commands."""

    def handle(self, request: Any) -> Optional[Any]:
        """Handle information commands."""
        if isinstance(request, dict):
            command = request.get("command", "").lower()
            context = request.get("context", {})

            if command == "look" or command == "l":
                return LookCommand(context)
            elif command == "inventory" or command == "inv" or command == "i":
                return InventoryCommand(context)
            elif command == "stats":
                return StatsCommand(context)

        return super().handle(request)


# ============= Command Processor =============

class CommandProcessor:
    """
    Main command processor.
    Manages command execution and history.

    GRASP Patterns:
    - Controller: Controls command processing
    - Low Coupling: Decouples UI from game logic
    """

    def __init__(self):
        """Initialize command processor."""
        self.command_history: List[ICommand] = []
        self.command_chain = self._build_command_chain()
        self.max_history = 50

    def _build_command_chain(self) -> IHandler:
        """Build chain of command handlers."""
        movement = MovementHandler()
        combat = CombatHandler()
        items = ItemHandler()
        info = InformationHandler()

        # Build chain
        movement.set_next(combat).set_next(items).set_next(info)

        return movement

    def process_input(self, input_str: str, game_context: Dict[str, Any]) -> bool:
        """
        Process player input.

        Args:
            input_str: Raw input string
            game_context: Game context

        Returns:
            True if command executed successfully
        """
        # Parse input
        parts = input_str.strip().split()
        if not parts:
            return False

        command_name = parts[0].lower()
        args = parts[1:]

        # Create request
        request = {
            "command": command_name,
            "args": args,
            "context": game_context
        }

        # Process through chain
        command = self.command_chain.handle(request)

        if command:
            success = command.execute()

            if success:
                # Add to history
                self.command_history.append(command)
                if len(self.command_history) > self.max_history:
                    self.command_history.pop(0)

            return success
        else:
            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": f"Unknown command: {command_name}",
                "type": "error"
            })
            return False

    def undo_last_command(self) -> bool:
        """
        Undo last command.

        Returns:
            True if undone successfully
        """
        if self.command_history:
            command = self.command_history.pop()
            command.undo()

            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": "Last action undone.",
                "type": "system"
            })
            return True

        return False

    def clear_history(self) -> None:
        """Clear command history."""
        self.command_history.clear()
