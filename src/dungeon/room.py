"""
Room and Dungeon implementation using Composite pattern.
Rooms can contain entities, items, and connections to other rooms.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.core.interfaces import (
    IComposite, IComponent, IVisitable, IVisitor,
    Direction, Position
)
from src.entities.base import Entity
from src.items.items import Item
from src.core.event_system import EventSystem, GameEvents


@dataclass
class RoomConnection:
    """Represents connection between rooms."""
    target_room: 'Room'
    direction: Direction
    locked: bool = False
    key_required: Optional[str] = None
    hidden: bool = False


class Room(IComposite, IVisitable):
    """
    Room implementation - Composite pattern.
    A room can contain entities, items, and connections to other rooms.

    GRASP Patterns:
    - Information Expert: Room knows about its contents and connections
    - Low Coupling: Room doesn't know about dungeon structure
    """

    def __init__(
        self,
        name: str,
        description: str,
        position: Optional[Position] = None,
        is_exit: bool = False
    ):
        """
        Initialize room.

        Args:
            name: Room name
            description: Room description
            position: Position in dungeon
            is_exit: Whether this is the dungeon exit
        """
        self.name = name
        self.description = description
        self.position = position or Position(0, 0)
        self.is_exit = is_exit

        self.entities: List[Entity] = []
        self.items: List[Item] = []
        self.connections: Dict[Direction, RoomConnection] = {}

        self.visited = False
        self.cleared = False
        self.light_level = 1.0  # 0.0 = pitch black, 1.0 = fully lit
        self.room_type = "normal"  # normal, treasure, boss, trap, safe

    # ============= IComposite Implementation =============

    def get_name(self) -> str:
        """Get room name."""
        return self.name

    def get_description(self) -> str:
        """Get room description with current state."""
        desc = self.description

        # Add visibility modifier
        if self.light_level < 0.3:
            desc = f"It's very dark here. {desc}"
        elif self.light_level < 0.7:
            desc = f"The room is dimly lit. {desc}"

        # Add room type hint
        if self.room_type == "treasure" and not self.cleared:
            desc += " You sense valuable items nearby."
        elif self.room_type == "boss":
            desc += " A powerful presence fills the room."
        elif self.room_type == "trap" and not self.cleared:
            desc += " Something doesn't feel right here."

        # Add exits
        if self.connections:
            exits = [dir.value for dir in self.connections.keys()]
            desc += f"\n\nExits: {', '.join(exits)}"

        # Add contents
        if self.entities:
            entity_names = [e.name for e in self.entities if e.is_alive()]
            if entity_names:
                desc += f"\n\nCreatures: {', '.join(entity_names)}"

        if self.items:
            item_names = [i.name for i in self.items]
            desc += f"\n\nItems: {', '.join(item_names)}"

        if self.is_exit:
            desc += "\n\n✨ This is the exit from the dungeon!"

        return desc

    def add(self, component: IComponent) -> bool:
        """
        Add entity or item to room.

        Args:
            component: Entity or Item to add

        Returns:
            True if added successfully
        """
        if isinstance(component, Entity):
            self.entities.append(component)
            return True
        elif isinstance(component, Item):
            self.items.append(component)
            return True
        return False

    def remove(self, component: IComponent) -> bool:
        """
        Remove entity or item from room.

        Args:
            component: Entity or Item to remove

        Returns:
            True if removed successfully
        """
        if isinstance(component, Entity) and component in self.entities:
            self.entities.remove(component)
            # Check if room is cleared
            if not any(e.is_alive() for e in self.entities):
                self.set_cleared()
            return True
        elif isinstance(component, Item) and component in self.items:
            self.items.remove(component)
            return True
        return False

    def get_children(self) -> List[IComponent]:
        """Get all entities and items in room."""
        return self.entities + self.items

    # ============= Room Management =============

    def add_connection(self, direction: Direction, target_room: 'Room',
                       locked: bool = False, key_required: str = None) -> None:
        """
        Add connection to another room.

        Args:
            direction: Direction of connection
            target_room: Target room
            locked: Whether connection is locked
            key_required: Key ID required to unlock
        """
        self.connections[direction] = RoomConnection(
            target_room=target_room,
            direction=direction,
            locked=locked,
            key_required=key_required
        )

        # Add reverse connection
        opposite = direction.opposite
        if opposite not in target_room.connections:
            target_room.connections[opposite] = RoomConnection(
                target_room=self,
                direction=opposite,
                locked=locked,
                key_required=key_required
            )

    def get_connection(self, direction: Direction) -> Optional[RoomConnection]:
        """
        Get connection in specified direction.

        Args:
            direction: Direction to check

        Returns:
            Room connection or None
        """
        return self.connections.get(direction)

    def can_move(self, direction: Direction) -> bool:
        """
        Check if movement in direction is possible.

        Args:
            direction: Direction to check

        Returns:
            True if movement is possible
        """
        connection = self.get_connection(direction)
        if not connection:
            return False

        if connection.locked:
            return False

        if connection.hidden and not self.cleared:
            return False

        return True

    def unlock_connection(self, direction: Direction, key_id: str) -> bool:
        """
        Attempt to unlock connection with key.

        Args:
            direction: Direction of connection
            key_id: Key identifier

        Returns:
            True if unlocked successfully
        """
        connection = self.get_connection(direction)
        if not connection or not connection.locked:
            return False

        if connection.key_required == key_id or key_id == "master":
            connection.locked = False
            # Also unlock from other side
            opposite = direction.opposite
            if opposite in connection.target_room.connections:
                connection.target_room.connections[opposite].locked = False

            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": f"Door to the {direction.value} unlocked!",
                "type": "unlock"
            })
            return True

        return False

    def enter(self, visitor: Entity = None) -> None:
        """
        Called when entity enters room.

        Args:
            visitor: Entity entering the room
        """
        if not self.visited:
            self.visited = True
            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": f"You discovered: {self.name}",
                "type": "discovery"
            })

        EventSystem().notify(GameEvents.ROOM_ENTERED, {
            "room": self,
            "visitor": visitor
        })

        # Trigger room-specific events
        if self.room_type == "trap" and not self.cleared:
            self._trigger_trap(visitor)

    def exit(self, visitor: Entity = None) -> None:
        """
        Called when entity exits room.

        Args:
            visitor: Entity exiting the room
        """
        EventSystem().notify(GameEvents.ROOM_EXITED, {
            "room": self,
            "visitor": visitor
        })

    def set_cleared(self) -> None:
        """Mark room as cleared."""
        if not self.cleared:
            self.cleared = True
            EventSystem().notify(GameEvents.ROOM_CLEARED, {
                "room": self
            })

            # Reveal hidden connections
            for connection in self.connections.values():
                if connection.hidden:
                    connection.hidden = False
                    EventSystem().notify(GameEvents.UI_MESSAGE, {
                        "message": f"A hidden passage to the {connection.direction.value} is revealed!",
                        "type": "discovery"
                    })

    def _trigger_trap(self, visitor: Entity) -> None:
        """
        Trigger room trap.

        Args:
            visitor: Entity triggering trap
        """
        import random
        trap_damage = random.randint(5, 15)

        EventSystem().notify(GameEvents.UI_WARNING, {
            "message": f"💀 Trap triggered! {visitor.name} takes {trap_damage} damage!",
            "type": "trap"
        })

        if visitor:
            visitor.take_damage(trap_damage)

        self.cleared = True  # Trap only triggers once

    def get_living_entities(self) -> List[Entity]:
        """Get all living entities in room."""
        return [e for e in self.entities if e.is_alive()]

    def has_hostile_entities(self) -> bool:
        """Check if room has hostile entities."""
        from src.core.interfaces import EntityType
        hostile_types = [EntityType.GOBLIN,
                         EntityType.SKELETON, EntityType.DRAGON]

        for entity in self.get_living_entities():
            if entity.entity_type in hostile_types:
                return True
        return False

    # ============= IVisitable Implementation =============

    def accept(self, visitor: IVisitor) -> Any:
        """Accept visitor for inspection."""
        return visitor.visit_room(self)

    # ============= String Representations =============

    def __str__(self) -> str:
        """String representation."""
        status = []
        if self.visited:
            status.append("Visited")
        if self.cleared:
            status.append("Cleared")
        if self.is_exit:
            status.append("EXIT")

        status_str = f" [{', '.join(status)}]" if status else ""
        return f"{self.name}{status_str}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Room(name='{self.name}', position={self.position}, type={self.room_type})"


class Dungeon(IComposite):
    """
    Dungeon - collection of rooms.
    Root of Composite pattern for dungeon structure.
    """

    def __init__(self, name: str = "The Dark Dungeon"):
        """
        Initialize dungeon.

        Args:
            name: Dungeon name
        """
        self.name = name
        self.rooms: List[Room] = []
        self.entrance: Optional[Room] = None
        self.exit: Optional[Room] = None
        self.current_room: Optional[Room] = None
        self.room_grid: Dict[Position, Room] = {}

    def get_name(self) -> str:
        """Get dungeon name."""
        return self.name

    def get_description(self) -> str:
        """Get dungeon description."""
        total_rooms = len(self.rooms)
        visited_rooms = sum(1 for r in self.rooms if r.visited)
        cleared_rooms = sum(1 for r in self.rooms if r.cleared)

        return (f"{self.name}\n"
                f"Rooms: {total_rooms} total, {visited_rooms} visited, {cleared_rooms} cleared")

    def add(self, component: IComponent) -> bool:
        """
        Add room to dungeon.

        Args:
            component: Room to add

        Returns:
            True if added successfully
        """
        if isinstance(component, Room):
            self.rooms.append(component)

            # Update grid
            if component.position:
                self.room_grid[component.position] = component

            # Set entrance/exit
            if not self.entrance:
                self.entrance = component
                self.current_room = component

            if component.is_exit:
                self.exit = component

            return True
        return False

    def remove(self, component: IComponent) -> bool:
        """
        Remove room from dungeon.

        Args:
            component: Room to remove

        Returns:
            True if removed successfully
        """
        if isinstance(component, Room) and component in self.rooms:
            self.rooms.remove(component)

            # Update grid
            if component.position in self.room_grid:
                del self.room_grid[component.position]

            return True
        return False

    def get_children(self) -> List[IComponent]:
        """Get all rooms."""
        return self.rooms.copy()

    def get_room_at(self, position: Position) -> Optional[Room]:
        """
        Get room at specific position.

        Args:
            position: Position to check

        Returns:
            Room at position or None
        """
        return self.room_grid.get(position)

    def find_room(self, name: str) -> Optional[Room]:
        """
        Find room by name.

        Args:
            name: Room name

        Returns:
            Room if found, None otherwise
        """
        for room in self.rooms:
            if room.name.lower() == name.lower():
                return room
        return None

    def get_adjacent_positions(self, position: Position) -> Dict[Direction, Position]:
        """
        Get adjacent positions.

        Args:
            position: Current position

        Returns:
            Dictionary of direction to position
        """
        return {
            Direction.NORTH: Position(position.x, position.y - 1),
            Direction.SOUTH: Position(position.x, position.y + 1),
            Direction.EAST: Position(position.x + 1, position.y),
            Direction.WEST: Position(position.x - 1, position.y)
        }

    def get_unexplored_rooms(self) -> List[Room]:
        """Get all unexplored rooms."""
        return [r for r in self.rooms if not r.visited]

    def get_treasure_rooms(self) -> List[Room]:
        """Get all treasure rooms."""
        return [r for r in self.rooms if r.room_type == "treasure"]

    def is_complete(self) -> bool:
        """Check if dungeon is complete (exit reached or all rooms cleared)."""
        if self.exit and self.exit.visited:
            return True

        return all(r.cleared for r in self.rooms if r.has_hostile_entities())

    def get_statistics(self) -> Dict[str, Any]:
        """Get dungeon statistics."""
        return {
            "name": self.name,
            "total_rooms": len(self.rooms),
            "visited_rooms": sum(1 for r in self.rooms if r.visited),
            "cleared_rooms": sum(1 for r in self.rooms if r.cleared),
            "treasure_rooms": len(self.get_treasure_rooms()),
            "unexplored_rooms": len(self.get_unexplored_rooms()),
            "completion_percentage": self._calculate_completion()
        }

    def _calculate_completion(self) -> float:
        """Calculate dungeon completion percentage."""
        if not self.rooms:
            return 0.0

        total_objectives = len(self.rooms)
        completed = sum(1 for r in self.rooms if r.cleared or r.visited)

        return (completed / total_objectives) * 100

    def __str__(self) -> str:
        """String representation."""
        return self.get_description()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Dungeon(name='{self.name}', rooms={len(self.rooms)})"
