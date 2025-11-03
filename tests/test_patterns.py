"""
Simple test demonstrating the design patterns in action.
Run with: python test_patterns.py
"""

from src.core.event_system import EventSystem, GameEvents
from src.combat.combat_system import get_combat_system, AggressiveStrategy
from src.dungeon.builders import SimpleDungeonBuilder
from src.items.inventory import get_item_factory, Inventory
from src.entities.factories import get_entity_factory
from src.core.interfaces import EntityType, ItemType
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_factory_pattern():
    """Test Abstract Factory and Prototype patterns."""
    print("\n=== Testing Factory Pattern ===")

    factory = get_entity_factory()

    # Create player
    player = factory.create(EntityType.PLAYER)
    print(f"Created: {player}")

    # Create monster
    goblin = factory.create(EntityType.GOBLIN)
    print(f"Created: {goblin}")

    # Clone monster (Prototype pattern)
    goblin_clone = goblin.clone()
    print(f"Cloned: {goblin_clone}")


def test_decorator_pattern():
    """Test Decorator pattern with weapons."""
    print("\n=== Testing Decorator Pattern ===")

    from src.items.items import Weapon, FlamingWeapon, FrostWeapon

    # Create basic weapon
    sword = Weapon("Iron Sword", "A standard sword", damage=10, value=50)
    print(f"Basic: {sword.get_description()}")

    # Decorate with fire
    flaming_sword = FlamingWeapon(sword)
    print(f"Decorated: {flaming_sword.get_description()}")

    # Double decoration
    frost_flaming_sword = FrostWeapon(flaming_sword)
    print(f"Double decorated: {frost_flaming_sword.get_description()}")


def test_composite_pattern():
    """Test Composite pattern with inventory and rooms."""
    print("\n=== Testing Composite Pattern ===")

    # Create inventory (Composite)
    inventory = Inventory("Test Inventory", capacity=10)

    # Add items
    item_factory = get_item_factory()
    sword = item_factory.create(ItemType.SWORD)
    potion = item_factory.create(ItemType.POTION)

    inventory.add(sword)
    inventory.add(potion)

    print(f"Inventory contents:\n{inventory}")


def test_builder_pattern():
    """Test Builder pattern for dungeon creation."""
    print("\n=== Testing Builder Pattern ===")

    builder = SimpleDungeonBuilder(size=3)
    dungeon = builder.build()

    print(f"Built dungeon: {dungeon}")
    print(f"Number of rooms: {len(dungeon.rooms)}")

    for room in dungeon.rooms[:3]:
        print(f"  - {room}")


def test_strategy_pattern():
    """Test Strategy pattern in combat."""
    print("\n=== Testing Strategy Pattern ===")

    combat_system = get_combat_system()

    # Create combatants
    factory = get_entity_factory()
    player = factory.create(EntityType.PLAYER)
    goblin = factory.create(EntityType.GOBLIN)

    # Set aggressive strategy
    combat_system.set_strategy(AggressiveStrategy())

    print(f"Combat between {player.name} and {goblin.name}")
    results = combat_system.execute_attack(player, goblin)

    print(
        f"Attack results: Hit={results['hit']}, Damage={results['damage']}, Critical={results['critical']}")


def test_observer_pattern():
    """Test Observer pattern with events."""
    print("\n=== Testing Observer Pattern ===")

    event_system = EventSystem()

    # Create a simple observer
    class TestObserver:
        def __init__(self, name):
            self.name = name
            self.events_received = []

        def update(self, event, data):
            self.events_received.append(event)
            print(f"{self.name} received event: {event}")

    # Attach observer
    observer = TestObserver("TestObserver")
    event_system.attach(observer, GameEvents.ENTITY_SPAWNED)

    # Trigger event
    event_system.notify(GameEvents.ENTITY_SPAWNED, {"entity": "TestEntity"})

    print(f"Observer received {len(observer.events_received)} events")


def test_state_pattern():
    """Test State pattern with game states."""
    print("\n=== Testing State Pattern ===")

    from src.core.game_state import MenuState, ExploringState
    from src.core.game_engine import get_game_engine

    engine = get_game_engine()

    # Create states
    menu_state = MenuState(engine)
    exploring_state = ExploringState(engine)

    print(f"Menu state type: {menu_state.state_type}")
    print(f"Exploring state type: {exploring_state.state_type}")

    # State transitions would be tested through game engine


def main():
    """Run all pattern tests."""
    print("=" * 60)
    print("DESIGN PATTERNS DEMONSTRATION")
    print("Dungeon Crawler - Architecture Test")
    print("=" * 60)

    test_factory_pattern()
    test_decorator_pattern()
    test_composite_pattern()
    test_builder_pattern()
    test_strategy_pattern()
    test_observer_pattern()
    test_state_pattern()

    print("\n" + "=" * 60)
    print("All pattern tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
