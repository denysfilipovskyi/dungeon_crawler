"""
Entity Factory implementation using Abstract Factory and Prototype patterns.
Creates different types of entities (monsters, player).
"""

from typing import Dict, Any

from src.core.interfaces import IFactory, EntityType, Stats
from src.entities.base import Entity, EntityBehavior, AggressiveBehavior, DefensiveBehavior


class EntityFactory(IFactory):
    """
    Abstract Factory pattern for creating entities.
    Combined with Prototype pattern for efficient object creation.

    GRASP Patterns:
    - Creator: Factory creates entities
    - Low Coupling: Factory isolates creation logic
    - Protected Variations: Shield client from entity creation changes
    """

    def __init__(self):
        """Initialize factory with prototype registry."""
        self._prototypes: Dict[EntityType, Entity] = {}
        self._behaviors: Dict[str, EntityBehavior] = {}
        self._initialize_prototypes()
        self._initialize_behaviors()

    def _initialize_prototypes(self) -> None:
        """
        Initialize prototype registry.
        These serve as templates for creating new entities.
        """
        # Player prototype
        self._prototypes[EntityType.PLAYER] = Entity(
            name="Hero",
            entity_type=EntityType.PLAYER,
            stats=Stats(health=100, max_health=100, attack=15, defense=5),
            behavior=None  # Player behavior is controlled by user
        )

        # Goblin prototype - weak but fast
        self._prototypes[EntityType.GOBLIN] = Entity(
            name="Goblin",
            entity_type=EntityType.GOBLIN,
            stats=Stats(health=30, max_health=30, attack=8, defense=2),
            behavior=AggressiveBehavior()
        )

        # Skeleton prototype - balanced
        self._prototypes[EntityType.SKELETON] = Entity(
            name="Skeleton",
            entity_type=EntityType.SKELETON,
            stats=Stats(health=50, max_health=50, attack=12, defense=4),
            behavior=DefensiveBehavior()
        )

        # Dragon prototype - boss enemy
        self._prototypes[EntityType.DRAGON] = Entity(
            name="Dragon",
            entity_type=EntityType.DRAGON,
            stats=Stats(health=200, max_health=200, attack=25, defense=10),
            behavior=DragonBehavior()
        )

    def _initialize_behaviors(self) -> None:
        """Initialize behavior registry for dynamic behavior assignment."""
        self._behaviors["aggressive"] = AggressiveBehavior()
        self._behaviors["defensive"] = DefensiveBehavior()
        self._behaviors["dragon"] = DragonBehavior()
        self._behaviors["cowardly"] = CowardlyBehavior()

    def create(self, entity_type: EntityType, **kwargs) -> Entity:
        """
        Create entity using Prototype pattern.

        Args:
            entity_type: Type of entity to create
            **kwargs: Additional parameters (name, stats_modifier, behavior)

        Returns:
            New entity instance
        """
        if entity_type not in self._prototypes:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Clone prototype
        entity = self._prototypes[entity_type].clone()

        # Apply customizations
        if "name" in kwargs:
            entity.name = kwargs["name"]

        if "stats_modifier" in kwargs:
            self._apply_stats_modifier(entity, kwargs["stats_modifier"])

        if "behavior" in kwargs:
            behavior_name = kwargs["behavior"]
            if behavior_name in self._behaviors:
                entity.behavior = self._behaviors[behavior_name]

        if "level" in kwargs:
            self._scale_to_level(entity, kwargs["level"])

        return entity

    def create_random_monster(self, difficulty: int = 1) -> Entity:
        """
        Create random monster based on difficulty.

        Args:
            difficulty: Difficulty level (1-10)

        Returns:
            Random monster entity
        """
        import random

        # Choose monster type based on difficulty
        if difficulty <= 3:
            monster_types = [EntityType.GOBLIN, EntityType.SKELETON]
        elif difficulty <= 7:
            monster_types = [EntityType.SKELETON, EntityType.GOBLIN]
        else:
            monster_types = [EntityType.SKELETON, EntityType.DRAGON]

        monster_type = random.choice(monster_types)

        # Create with level scaling
        return self.create(
            entity_type=monster_type,
            level=difficulty
        )

    def register_prototype(self, entity_type: EntityType, prototype: Entity) -> None:
        """
        Register new prototype for entity type.
        Allows runtime extension of factory.

        Args:
            entity_type: Type to register
            prototype: Prototype entity
        """
        self._prototypes[entity_type] = prototype

    def register_behavior(self, name: str, behavior: EntityBehavior) -> None:
        """
        Register new behavior.

        Args:
            name: Behavior name
            behavior: Behavior implementation
        """
        self._behaviors[name] = behavior

    @staticmethod
    def _apply_stats_modifier(entity: Entity, modifier: Dict[str, int]) -> None:
        """
        Apply stats modifications to entity.

        Args:
            entity: Entity to modify
            modifier: Stats modifications
        """
        if "health" in modifier:
            entity.stats.max_health += modifier["health"]
            entity.stats.health += modifier["health"]
        if "attack" in modifier:
            entity.stats.attack += modifier["attack"]
        if "defense" in modifier:
            entity.stats.defense += modifier["defense"]

    @staticmethod
    def _scale_to_level(entity: Entity, level: int) -> None:
        """
        Scale entity stats to level.

        Args:
            entity: Entity to scale
            level: Target level
        """
        scale_factor = 1 + (level - 1) * 0.2
        entity.stats.max_health = int(entity.stats.max_health * scale_factor)
        entity.stats.health = entity.stats.max_health
        entity.stats.attack = int(entity.stats.attack * scale_factor)
        entity.stats.defense = int(entity.stats.defense * scale_factor)


# ============= Specialized Factories (Abstract Factory variants) =============

class MonsterFactory(EntityFactory):
    """
    Specialized factory for creating monsters.
    Example of Abstract Factory specialization.
    """

    def create_pack(self, monster_type: EntityType, count: int = 3) -> list[Entity]:
        """
        Create a pack of monsters.

        Args:
            monster_type: Type of monsters
            count: Number of monsters

        Returns:
            List of monsters
        """
        pack = []
        for i in range(count):
            monster = self.create(
                entity_type=monster_type,
                name=f"{monster_type.value.capitalize()} #{i+1}"
            )
            # Make pack members slightly weaker
            monster.stats.health = int(monster.stats.health * 0.8)
            monster.stats.max_health = int(monster.stats.max_health * 0.8)
            pack.append(monster)
        return pack

    def create_elite(self, monster_type: EntityType) -> Entity:
        """
        Create elite version of monster.

        Args:
            monster_type: Base monster type

        Returns:
            Elite monster
        """
        elite = self.create(
            entity_type=monster_type,
            name=f"Elite {monster_type.value.capitalize()}",
            stats_modifier={
                "health": 20,
                "attack": 5,
                "defense": 3
            }
        )
        elite.apply_status_effect("elite", -1)  # Permanent effect
        return elite


class BossFactory(EntityFactory):
    """
    Specialized factory for creating boss enemies.
    """

    def create_boss(self, name: str, difficulty: int) -> Entity:
        """
        Create unique boss enemy.

        Args:
            name: Boss name
            difficulty: Boss difficulty

        Returns:
            Boss entity
        """
        # Always use Dragon as base for bosses
        boss = self.create(
            entity_type=EntityType.DRAGON,
            name=name,
            level=difficulty
        )

        # Add boss-specific enhancements
        boss.stats.max_health *= 2
        boss.stats.health = boss.stats.max_health
        boss.apply_status_effect("boss", -1)  # Permanent boss status

        return boss


# ============= Additional Behaviors =============

class DragonBehavior(EntityBehavior):
    """Special behavior for dragon enemies."""

    def __init__(self):
        self.rage_triggered = False

    def on_spawn(self, entity: Entity) -> None:
        """Epic spawn message."""
        from src.core.event_system import EventSystem, GameEvents
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"🐉 {entity.name} awakens from its slumber! The ground trembles!",
            "type": "boss_spawn"
        })

    def on_death(self, entity: Entity) -> None:
        """Epic death message."""
        from src.core.event_system import EventSystem, GameEvents
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"🏆 {entity.name} has been slain! You are victorious!",
            "type": "boss_death"
        })

    def on_damage_taken(self, entity: Entity, amount: int) -> int:
        """Rage mode when health drops below 50%."""
        if not self.rage_triggered and entity.stats.health < entity.stats.max_health * 0.5:
            self.rage_triggered = True
            entity.stats.attack *= 2
            entity.apply_status_effect("enraged", -1)

            from src.core.event_system import EventSystem, GameEvents
            EventSystem().notify(GameEvents.UI_MESSAGE, {
                "message": f"💢 {entity.name} enters a berserker rage!",
                "type": "boss_rage"
            })

        return amount

    def on_turn_start(self, entity: Entity) -> None:
        """Regenerate health slowly."""
        entity.update_status_effects()
        if entity.stats.health < entity.stats.max_health:
            entity.heal(5)

    def get_action(self, entity: Entity, context: Dict[str, Any]) -> str:
        """Dragon AI - uses special attacks."""
        import random

        if context.get("player_in_range", False):
            if self.rage_triggered:
                # Always attack in rage mode
                return "fire_breath" if random.random() < 0.5 else "attack"
            else:
                # Mix of attacks and defense
                action_weights = [
                    ("attack", 0.4),
                    ("fire_breath", 0.3),
                    ("defend", 0.2),
                    ("tail_sweep", 0.1)
                ]

                rand = random.random()
                cumulative = 0
                for action, weight in action_weights:
                    cumulative += weight
                    if rand < cumulative:
                        return action

        return "wait"


class CowardlyBehavior(EntityBehavior):
    """Behavior for cowardly enemies that flee when injured."""

    def on_spawn(self, entity: Entity) -> None:
        """Nervous spawn."""
        from src.core.event_system import EventSystem, GameEvents
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} appears, looking nervous...",
            "type": "spawn"
        })

    def on_death(self, entity: Entity) -> None:
        """Pitiful death."""
        from src.core.event_system import EventSystem, GameEvents
        EventSystem().notify(GameEvents.UI_MESSAGE, {
            "message": f"{entity.name} whimpers and collapses.",
            "type": "death"
        })

    def on_damage_taken(self, entity: Entity, amount: int) -> int:
        """Panic when damaged."""
        if entity.stats.health < entity.stats.max_health * 0.5:
            entity.apply_status_effect("panicked", 3)
        return amount

    def on_turn_start(self, entity: Entity) -> None:
        """Update effects."""
        entity.update_status_effects()

    def get_action(self, entity: Entity, context: Dict[str, Any]) -> str:
        """Flee when injured, attack when healthy."""
        health_percentage = entity.stats.health / entity.stats.max_health

        if health_percentage < 0.3:
            return "flee"
        elif health_percentage < 0.6:
            return "defend"
        elif context.get("player_in_range", False):
            return "attack"

        return "wait"


# ============= Factory Singleton Instance =============

def get_entity_factory() -> EntityFactory:
    """
    Get singleton instance of entity factory.

    Returns:
        Entity factory instance
    """
    if not hasattr(get_entity_factory, "_instance"):
        get_entity_factory._instance = EntityFactory()
    return get_entity_factory._instance
