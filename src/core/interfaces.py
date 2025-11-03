"""
Core interfaces and abstract base classes.
Following Interface Segregation Principle (ISP) - many specific interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.entities.base import Entity
    from src.items.base import Item
    from src.dungeon.room import Room


# ============= ENUMS =============

class Direction(Enum):
    """Enumeration for movement directions."""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

    @property
    def opposite(self):
        """Get opposite direction."""
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return opposites[self]


class GameStateType(Enum):
    """Game state types for State pattern."""
    MENU = "menu"
    EXPLORING = "exploring"
    COMBAT = "combat"
    INVENTORY = "inventory"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class EntityType(Enum):
    """Entity types for factory pattern."""
    PLAYER = "player"
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    DRAGON = "dragon"


class ItemType(Enum):
    """Item types for factory pattern."""
    SWORD = "sword"
    SHIELD = "shield"
    POTION = "potion"
    KEY = "key"


# ============= DATA CLASSES =============

@dataclass
class Stats:
    """Entity statistics - Data class pattern."""
    health: int
    max_health: int
    attack: int
    defense: int

    def __str__(self):
        return f"HP: {self.health}/{self.max_health}, ATK: {self.attack}, DEF: {self.defense}"


@dataclass
class Position:
    """Position in dungeon."""
    x: int
    y: int

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


# ============= CORE INTERFACES =============

class IObserver(ABC):
    """Observer pattern - Observer interface."""

    @abstractmethod
    def update(self, event: str, data: Dict[str, Any]) -> None:
        """Receive notification about event."""
        pass


class IObservable(ABC):
    """Observer pattern - Subject interface."""

    @abstractmethod
    def attach(self, observer: IObserver) -> None:
        """Attach an observer."""
        pass

    @abstractmethod
    def detach(self, observer: IObserver) -> None:
        """Detach an observer."""
        pass

    @abstractmethod
    def notify(self, event: str, data: Dict[str, Any]) -> None:
        """Notify all observers about event."""
        pass


class ICommand(ABC):
    """Command pattern interface."""

    @abstractmethod
    def execute(self) -> bool:
        """Execute command. Returns True if successful."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Undo command if possible."""
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        """Check if command can be executed."""
        pass


class IState(ABC):
    """State pattern interface for game states."""

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
        """Handle player input. Returns new state if transition needed."""
        pass

    @abstractmethod
    def update(self) -> Optional['IState']:
        """Update state. Returns new state if transition needed."""
        pass


# ============= ENTITY INTERFACES =============

class IDamageable(ABC):
    """Interface for entities that can take damage."""

    @abstractmethod
    def take_damage(self, amount: int) -> None:
        """Apply damage to entity."""
        pass

    @abstractmethod
    def heal(self, amount: int) -> None:
        """Heal entity."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Check if entity is still alive."""
        pass


class IAttacker(ABC):
    """Interface for entities that can attack."""

    @abstractmethod
    def calculate_damage(self) -> int:
        """Calculate damage for attack."""
        pass

    @abstractmethod
    def attack(self, target: IDamageable) -> None:
        """Perform attack on target."""
        pass


class ICombatant(IDamageable, IAttacker):
    """Combined interface for combat-capable entities."""

    @abstractmethod
    def get_stats(self) -> Stats:
        """Get entity statistics."""
        pass

    @abstractmethod
    def defend(self) -> None:
        """Take defensive stance."""
        pass


# ============= FACTORY INTERFACES =============

class IFactory(ABC):
    """Abstract Factory pattern interface."""

    @abstractmethod
    def create(self, type: Enum, **kwargs) -> Any:
        """Create object of specified type."""
        pass


class IBuilder(ABC):
    """Builder pattern interface."""

    @abstractmethod
    def reset(self) -> None:
        """Reset builder to initial state."""
        pass

    @abstractmethod
    def build(self) -> Any:
        """Build and return the final product."""
        pass


class IPrototype(ABC):
    """Prototype pattern interface."""

    @abstractmethod
    def clone(self) -> 'IPrototype':
        """Create a copy of this object."""
        pass


# ============= STRATEGY INTERFACES =============

class ICombatStrategy(ABC):
    """Strategy pattern for combat behavior."""

    @abstractmethod
    def execute_turn(self, attacker: ICombatant, defender: ICombatant) -> Dict[str, Any]:
        """Execute combat turn with specific strategy."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get strategy description."""
        pass


class IMovementStrategy(ABC):
    """Strategy pattern for movement behavior."""

    @abstractmethod
    def can_move(self, from_room: 'Room', direction: Direction) -> bool:
        """Check if movement is possible."""
        pass

    @abstractmethod
    def move(self, from_room: 'Room', direction: Direction) -> Optional['Room']:
        """Execute movement."""
        pass


# ============= VISITOR INTERFACES =============

class IVisitor(ABC):
    """Visitor pattern interface."""

    @abstractmethod
    def visit_entity(self, entity: 'Entity') -> Any:
        """Visit entity."""
        pass

    @abstractmethod
    def visit_item(self, item: 'Item') -> Any:
        """Visit item."""
        pass

    @abstractmethod
    def visit_room(self, room: 'Room') -> Any:
        """Visit room."""
        pass


class IVisitable(ABC):
    """Interface for objects that can be visited."""

    @abstractmethod
    def accept(self, visitor: IVisitor) -> Any:
        """Accept visitor."""
        pass


# ============= MEMENTO INTERFACES =============

class IMemento(ABC):
    """Memento pattern interface for save game."""

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get saved state."""
        pass


class IOriginator(ABC):
    """Interface for objects that can create mementos."""

    @abstractmethod
    def create_memento(self) -> IMemento:
        """Create memento with current state."""
        pass

    @abstractmethod
    def restore_from_memento(self, memento: IMemento) -> None:
        """Restore state from memento."""
        pass


# ============= COMPONENT INTERFACES =============

class IComponent(ABC):
    """Composite pattern - Component interface."""

    @abstractmethod
    def get_name(self) -> str:
        """Get component name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get component description."""
        pass


class IComposite(IComponent):
    """Composite pattern - Composite interface."""

    @abstractmethod
    def add(self, component: IComponent) -> None:
        """Add child component."""
        pass

    @abstractmethod
    def remove(self, component: IComponent) -> None:
        """Remove child component."""
        pass

    @abstractmethod
    def get_children(self) -> List[IComponent]:
        """Get all children."""
        pass


# ============= DECORATOR INTERFACES =============

class IDecorator(IComponent):
    """Decorator pattern interface."""

    @abstractmethod
    def get_wrapped(self) -> IComponent:
        """Get wrapped component."""
        pass


# ============= CHAIN OF RESPONSIBILITY =============

class IHandler(ABC):
    """Chain of Responsibility pattern interface."""

    @abstractmethod
    def set_next(self, handler: 'IHandler') -> 'IHandler':
        """Set next handler in chain."""
        pass

    @abstractmethod
    def handle(self, request: Any) -> Optional[Any]:
        """Handle request or pass to next handler."""
        pass
