"""
Base Entity classes implementing Bridge pattern.
Separates entity abstraction from behavior implementation.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import copy

from src.core.interfaces import (
    ICombatant, IPrototype, IVisitable, IVisitor,
    Stats, EntityType, IMemento, IOriginator
)
from src.core.event_system import EventSystem, GameEvents


class EntityBehavior(ABC):
    """
    Bridge pattern - Implementation side.
    Defines behavior interface for entities.
    """

    @abstractmethod
    def on_spawn(self, entity: 'Entity') -> None:
        """Called when entity spawns."""
        pass

    @abstractmethod
    def on_death(self, entity: 'Entity') -> None:
        """Called when entity dies."""
        pass

    @abstractmethod
    def on_damage_taken(self, entity: 'Entity', amount: int) -> int:
        """Called when entity takes damage. Can modify damage amount."""
        pass

    @abstractmethod
    def on_turn_start(self, entity: 'Entity') -> None:
        """Called at the start of entity's turn."""
        pass

    @abstractmethod
    def get_action(self, entity: 'Entity', context: Dict[str, Any]) -> str:
        """Determine entity's action (AI behavior)."""
        pass


class Entity(ICombatant, IPrototype, IVisitable, IOriginator):
    """
    Base Entity class - Bridge pattern abstraction side.
    Represents all living creatures in the game.

    Design Patterns:
    - Bridge: Separates entity from behavior
    - Prototype: Can be cloned
    - Template Method: Defines skeleton of operations
    - Visitor: Can accept visitors for inspection
    - Memento: Can save/restore state
    """

    def __init__(
        self,
        name: str,
        entity_type: EntityType,
        stats: Stats,
        behavior: Optional[EntityBehavior] = None
    ):
        """
        Initialize entity.

        Args:
            name: Entity name
            entity_type: Type of entity
            stats: Entity statistics
            behavior: Bridge to behavior implementation
        """
        self.name = name
        self.entity_type = entity_type
        self.stats = copy.deepcopy(stats)  # Defensive copy
        self.behavior = behavior or DefaultBehavior()
        self.is_defending = False
        self.status_effects: Dict[str, int] = {}  # effect_name -> duration
        self.event_system = EventSystem()

        # Notify about spawn
        self.behavior.on_spawn(self)
        self.event_system.notify(GameEvents.ENTITY_SPAWNED, {
            "entity": self,
            "entity_type": self.entity_type.value,
            "position": None  # Will be set by room
        })

    # ============= ICombatant Implementation =============

    def take_damage(self, amount: int) -> None:
        """
        Apply damage to entity (Template Method pattern).

        Args:
            amount: Damage amount
        """
        # Let behavior modify damage (Bridge pattern)
        modified_damage = self.behavior.on_damage_taken(self, amount)

        # Apply defense reduction
        if self.is_defending:
            modified_damage = max(0, modified_damage - self.stats.defense)
            self.is_defending = False

        # Apply damage
        actual_damage = min(self.stats.health, modified_damage)
        self.stats.health -= actual_damage

        # Notify about damage
        self.event_system.notify(GameEvents.ENTITY_DAMAGED, {
            "entity": self,
            "damage": actual_damage,
            "remaining_health": self.stats.health
        })

        # Check for death
        if not self.is_alive():
            self._die()

    def heal(self, amount: int) -> None:
        """
        Heal entity.

        Args:
            amount: Healing amount
        """
        actual_heal = min(amount, self.stats.max_health - self.stats.health)
        self.stats.health += actual_heal

        self.event_system.notify(GameEvents.ENTITY_DAMAGED, {
            "entity": self,
            "healing": actual_heal,
            "remaining_health": self.stats.health
        })

    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.stats.health > 0

    def calculate_damage(self) -> int:
        """Calculate base damage for attack."""
        base_damage = self.stats.attack

        # Apply status effects
        if "strength" in self.status_effects:
            base_damage = int(base_damage * 1.5)
        if "weakness" in self.status_effects:
            base_damage = int(base_damage * 0.5)

        return base_damage

    def attack(self, target: ICombatant) -> None:
        """
        Perform attack on target.

        Args:
            target: Attack target
        """
        damage = self.calculate_damage()
        target.take_damage(damage)

        event_type = GameEvents.PLAYER_ATTACKED if self.entity_type == EntityType.PLAYER else GameEvents.COMBAT_TURN

        self.event_system.notify(
            event_type, {
                "attacker": self,
                "target": target,
                "damage": damage
            }
        )

    def get_stats(self) -> Stats:
        """Get entity statistics."""
        return copy.deepcopy(self.stats)  # Return defensive copy

    def defend(self) -> None:
        """Take defensive stance."""
        self.is_defending = True

        if self.entity_type == EntityType.PLAYER:
            self.event_system.notify(
                GameEvents.PLAYER_DEFENDED, {"entity": self})

    # ============= Status Effects =============

    def apply_status_effect(self, effect: str, duration: int) -> None:
        """
        Apply status effect to entity.

        Args:
            effect: Effect name
            duration: Duration in turns
        """
        self.status_effects[effect] = duration

    def update_status_effects(self) -> None:
        """Update status effects (called each turn)."""
        effects_to_remove = []

        for effect, duration in self.status_effects.items():
            self.status_effects[effect] = duration - 1
            if self.status_effects[effect] <= 0:
                effects_to_remove.append(effect)

        for effect in effects_to_remove:
            del self.status_effects[effect]

    # ============= IPrototype Implementation =============

    def clone(self) -> 'Entity':
        """
        Create a deep copy of this entity (Prototype pattern).

        Returns:
            Cloned entity
        """
        cloned = Entity(
            name=f"{self.name} (Clone)",
            entity_type=self.entity_type,
            stats=copy.deepcopy(self.stats),
            behavior=self.behavior  # Share behavior (Flyweight-like)
        )
        cloned.status_effects = copy.deepcopy(self.status_effects)
        return cloned

    # ============= IVisitable Implementation =============

    def accept(self, visitor: IVisitor) -> Any:
        """
        Accept visitor (Visitor pattern).

        Args:
            visitor: Visitor to accept

        Returns:
            Visitor result
        """
        return visitor.visit_entity(self)

    # ============= IOriginator Implementation (Memento) =============

    def create_memento(self) -> IMemento:
        """
        Create memento with current state.

        Returns:
            Memento object
        """
        return EntityMemento({
            'name': self.name,
            'entity_type': self.entity_type.value,
            'stats': {
                'health': self.stats.health,
                'max_health': self.stats.max_health,
                'attack': self.stats.attack,
                'defense': self.stats.defense
            },
            'status_effects': copy.deepcopy(self.status_effects),
            'is_defending': self.is_defending
        })

    def restore_from_memento(self, memento: IMemento) -> None:
        """
        Restore state from memento.

        Args:
            memento: Memento to restore from
        """
        state = memento.get_state()
        self.name = state['name']
        self.entity_type = EntityType(state['entity_type'])
        self.stats.health = state['stats']['health']
        self.stats.max_health = state['stats']['max_health']
        self.stats.attack = state['stats']['attack']
        self.stats.defense = state['stats']['defense']
        self.status_effects = state['status_effects']
        self.is_defending = state['is_defending']

    # ============= Private Methods =============

    def _die(self) -> None:
        """Handle entity death."""
        self.behavior.on_death(self)

        event = GameEvents.PLAYER_DIED if self.entity_type == EntityType.PLAYER else GameEvents.ENTITY_DIED
        self.event_system.notify(event, {
            "entity": self,
            "entity_type": self.entity_type.value
        })

    # ============= Magic Methods =============

    def __str__(self) -> str:
        """String representation."""
        status = "Defending" if self.is_defending else "Normal"
        effects = ", ".join(self.status_effects.keys()
                            ) if self.status_effects else "None"
        return f"{self.name} ({self.entity_type.value}) - {self.stats} - Status: {status} - Effects: {effects}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Entity(name='{self.name}', type={self.entity_type},health={self.stats.health}/{self.stats.max_health})"


# ============= Concrete Behaviors (Bridge Implementation) =============

class DefaultBehavior(EntityBehavior):
    """Default passive behavior."""

    def on_spawn(self, entity: Entity) -> None:
        """Do nothing on spawn."""
        pass

    def on_death(self, entity: Entity) -> None:
        """Do nothing on death."""
        pass

    def on_damage_taken(self, entity: Entity, amount: int) -> int:
        """Return unmodified damage."""
        return amount

    def on_turn_start(self, entity: Entity) -> None:
        """Update status effects."""
        entity.update_status_effects()

    def get_action(self, entity: Entity, context: Dict[str, Any]) -> str:
        """Always wait."""
        return "wait"


class AggressiveBehavior(EntityBehavior):
    """Aggressive AI behavior - always attacks."""

    def on_spawn(self, entity: Entity) -> None:
        """Roar on spawn!"""
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} appears with a fierce roar!",
            "type": "spawn"
        })

    def on_death(self, entity: Entity) -> None:
        """Death message."""
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} falls in battle!",
            "type": "death"
        })

    def on_damage_taken(self, entity: Entity, amount: int) -> int:
        """Enrage when damaged - reduce damage but increase attack."""
        if amount > 5:
            entity.apply_status_effect("enraged", 3)
            entity.stats.attack += 2
            return int(amount * 0.8)  # Reduce damage by 20%
        return amount

    def on_turn_start(self, entity: Entity) -> None:
        """Update effects and possibly heal."""
        entity.update_status_effects()
        # Small chance to regenerate
        import random
        if random.random() < 0.1:
            entity.heal(2)

    def get_action(self, entity: Entity, context: Dict[str, Any]) -> str:
        """Always choose to attack if possible."""
        if context.get("player_in_range", False):
            return "attack"
        return "move_towards_player"


class DefensiveBehavior(EntityBehavior):
    """Defensive AI behavior - alternates between defense and attack."""

    def __init__(self):
        self.turn_counter = 0

    def on_spawn(self, entity: Entity) -> None:
        """Defensive stance on spawn."""
        entity.defend()
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} takes a defensive stance.",
            "type": "spawn"
        })

    def on_death(self, entity: Entity) -> None:
        """Death message."""
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} has been defeated.",
            "type": "death"
        })

    def on_damage_taken(self, entity: Entity, amount: int) -> int:
        """Increase defense when low health."""
        if entity.stats.health < entity.stats.max_health * 0.3:
            return int(amount * 0.5)  # Half damage when critically injured
        return amount

    def on_turn_start(self, entity: Entity) -> None:
        """Update turn counter and effects."""
        self.turn_counter += 1
        entity.update_status_effects()

    def get_action(self, entity: Entity, context: Dict[str, Any]) -> str:
        """Alternate between attack and defense."""
        if context.get("player_in_range", False):
            if self.turn_counter % 2 == 0:
                return "defend"
            else:
                return "attack"
        return "wait"


# ============= Memento Implementation =============

class EntityMemento(IMemento):
    """Memento for Entity state."""

    def __init__(self, state: Dict[str, Any]):
        """Store entity state."""
        self._state = copy.deepcopy(state)

    def get_state(self) -> Dict[str, Any]:
        """Get stored state."""
        return copy.deepcopy(self._state)
