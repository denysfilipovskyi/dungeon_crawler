"""
Inventory system using Composite pattern.
Item Factory for creating various items.
"""

from typing import List, Optional, Dict, Any
import random

from src.core.interfaces import (
    IComposite, IComponent, IFactory, ItemType, IVisitor
)
from src.items.items import (
    Item, Weapon, Shield, Potion, Key,
    FlamingWeapon, FrostWeapon, VampiricWeapon, LegendaryWeapon
)
from src.core.event_system import EventSystem, GameEvents


class Inventory(IComposite):
    """
    Inventory implementation using Composite pattern.
    Can contain items and sub-inventories (bags, containers).

    GRASP Patterns:
    - Information Expert: Inventory knows about its items
    - High Cohesion: All inventory operations in one place
    """

    def __init__(
        self,
        name: str = "Inventory",
        capacity: int = 20
    ):
        """
        Initialize inventory.

        Args:
            name: Inventory name
            capacity: Maximum number of items
        """
        self.name = name
        self.capacity = capacity
        self._items: List[IComponent] = []
        self._equipped_items: Dict[ItemType, Item] = {}

    def get_name(self) -> str:
        """Get inventory name."""
        return self.name

    def get_description(self) -> str:
        """Get inventory description."""
        return f"{self.name} ({len(self._items)}/{self.capacity} items)"

    def add(self, component: IComponent) -> bool:
        """
        Add item or sub-inventory.

        Args:
            component: Item or sub-inventory to add

        Returns:
            True if added successfully
        """
        if len(self._items) >= self.capacity:
            EventSystem().notify(GameEvents.UI_WARNING, {
                "message": f"{self.name} is full!"
            })
            return False

        self._items.append(component)

        if isinstance(component, Item):
            EventSystem().notify(GameEvents.ITEM_PICKED_UP, {
                "item": component,
                "inventory": self
            })

        return True

    def remove(self, component: IComponent) -> bool:
        """
        Remove item or sub-inventory.

        Args:
            component: Item or sub-inventory to remove

        Returns:
            True if removed successfully
        """
        if component in self._items:
            self._items.remove(component)

            if isinstance(component, Item):
                EventSystem().notify(GameEvents.ITEM_DROPPED, {
                    "item": component,
                    "inventory": self
                })

            return True
        return False

    def get_children(self) -> List[IComponent]:
        """Get all items and sub-inventories."""
        return self._items.copy()

    def find_item(self, name: str) -> Optional[Item]:
        """
        Find item by name (recursive search).

        Args:
            name: Item name to search for

        Returns:
            Item if found, None otherwise
        """
        for component in self._items:
            if isinstance(component, Item):
                if component.get_name().lower() == name.lower():
                    return component
            elif isinstance(component, Inventory):
                # Recursive search in sub-inventories
                found = component.find_item(name)
                if found:
                    return found
        return None

    def find_items_by_type(self, item_type: ItemType) -> List[Item]:
        """
        Find all items of specific type.

        Args:
            item_type: Type of items to find

        Returns:
            List of items
        """
        items = []
        for component in self._items:
            if isinstance(component, Item):
                if component.item_type == item_type:
                    items.append(component)
            elif isinstance(component, Inventory):
                # Recursive search
                items.extend(component.find_items_by_type(item_type))
        return items

    def equip_item(self, item: Item, user: Any) -> bool:
        """
        Equip an item.

        Args:
            item: Item to equip
            user: Entity equipping the item

        Returns:
            True if equipped successfully
        """
        if item not in self._items:
            return False

        # Unequip current item of same type
        if item.item_type in self._equipped_items:
            current = self._equipped_items[item.item_type]
            current.unequip(user)

        # Equip new item
        if item.equip(user):
            self._equipped_items[item.item_type] = item
            return True

        return False

    def unequip_item(self, item_type: ItemType, user: Any) -> bool:
        """
        Unequip item of specific type.

        Args:
            item_type: Type of item to unequip
            user: Entity unequipping the item

        Returns:
            True if unequipped successfully
        """
        if item_type in self._equipped_items:
            item = self._equipped_items[item_type]
            if item.unequip(user):
                del self._equipped_items[item_type]
                return True
        return False

    def get_equipped_items(self) -> Dict[ItemType, Item]:
        """Get all equipped items."""
        return self._equipped_items.copy()

    def get_total_weight(self) -> int:
        """Calculate total weight of inventory."""
        total = 0
        for component in self._items:
            if isinstance(component, Item):
                total += component.weight
            elif isinstance(component, Inventory):
                total += component.get_total_weight()
        return total

    def get_total_value(self) -> int:
        """Calculate total value of inventory."""
        total = 0
        for component in self._items:
            if isinstance(component, Item):
                total += component.value
            elif isinstance(component, Inventory):
                total += component.get_total_value()
        return total

    def accept(self, visitor: IVisitor) -> Any:
        """Accept visitor for inventory inspection."""
        # Visit inventory itself
        result = [visitor.visit_item(self)]

        # Visit all items
        for component in self._items:
            if hasattr(component, 'accept'):
                result.append(component.accept(visitor))

        return result

    def __str__(self) -> str:
        """String representation."""
        if not self._items:
            return f"{self.name} (Empty)"

        items_str = "\n  ".join([str(item) for item in self._items])
        return f"{self.name} ({len(self._items)}/{self.capacity}):\n  {items_str}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Inventory(name='{self.name}', items={len(self._items)}, capacity={self.capacity})"


# ============= Item Factory =============

class ItemFactory(IFactory):
    """
    Factory for creating items.
    Uses Factory Method and Prototype patterns.

    GRASP Patterns:
    - Creator: Factory creates items
    - Protected Variations: Shields clients from item creation changes
    """

    def __init__(self):
        """Initialize item factory with templates."""
        self._item_templates = self._initialize_templates()
        self._enchantment_chance = 0.1  # 10% chance for enchantment

    def _initialize_templates(self) -> Dict[str, Item]:
        """
        Initialize item templates (prototypes).

        Returns:
            Dictionary of item templates
        """
        return {
            # Weapons
            "rusty_sword": Weapon("Rusty Sword", "An old, worn sword", damage=5, value=10),
            "iron_sword": Weapon("Iron Sword", "A standard iron sword", damage=10, value=50),
            "steel_sword": Weapon("Steel Sword", "A sharp steel blade", damage=15, value=100),
            "mythril_sword": Weapon("Mythril Sword", "A legendary mythril blade", damage=25, value=500),

            # Shields
            "wooden_shield": Shield("Wooden Shield", "A simple wooden shield", defense=3, value=15),
            "iron_shield": Shield("Iron Shield", "A sturdy iron shield", defense=5, value=60),
            "tower_shield": Shield("Tower Shield", "A massive protective shield", defense=10, value=150),

            # Potions
            "small_potion": Potion("Small Potion", "Restores a small amount of health", healing=25, value=10),
            "health_potion": Potion("Health Potion", "Restores health", healing=50, value=25),
            "large_potion": Potion("Large Potion", "Restores a large amount of health", healing=100, value=60),

            # Keys
            "iron_key": Key("Iron Key", "A simple iron key", key_id="iron"),
            "gold_key": Key("Gold Key", "An ornate golden key", key_id="gold"),
            "master_key": Key("Master Key", "Opens any lock", key_id="master"),
        }

    def create(self, item_type: ItemType, **kwargs) -> Item:
        """
        Create item of specified type.

        Args:
            item_type: Type of item to create
            **kwargs: Additional parameters (level, quality, enchanted)

        Returns:
            Created item
        """
        # Determine specific item based on type and parameters
        level = kwargs.get("level", 1)
        quality = kwargs.get("quality", "normal")

        item = self._create_base_item(item_type, level, quality)

        # Apply enchantments if specified or random chance
        if kwargs.get("enchanted", False) or random.random() < self._enchantment_chance:
            if isinstance(item, Weapon):
                item = self._enchant_weapon(item, level)

        return item

    def _create_base_item(self, item_type: ItemType, level: int, quality: str) -> Item:
        """
        Create base item based on type and level.

        Args:
            item_type: Type of item
            level: Item level (affects quality)
            quality: Item quality tier

        Returns:
            Base item
        """
        if item_type == ItemType.SWORD:
            if level <= 3:
                template_key = "rusty_sword"
            elif level <= 6:
                template_key = "iron_sword"
            elif level <= 9:
                template_key = "steel_sword"
            else:
                template_key = "mythril_sword"

        elif item_type == ItemType.SHIELD:
            if level <= 4:
                template_key = "wooden_shield"
            elif level <= 8:
                template_key = "iron_shield"
            else:
                template_key = "tower_shield"

        elif item_type == ItemType.POTION:
            if level <= 3:
                template_key = "small_potion"
            elif level <= 7:
                template_key = "health_potion"
            else:
                template_key = "large_potion"

        elif item_type == ItemType.KEY:
            if level <= 5:
                template_key = "iron_key"
            elif level <= 9:
                template_key = "gold_key"
            else:
                template_key = "master_key"

        else:
            # Default to potion
            template_key = "health_potion"

        # Clone template
        item = self._item_templates[template_key].clone()

        # Apply quality modifiers
        if quality == "superior" and hasattr(item, 'damage'):
            item.damage = int(item.damage * 1.2)
            item.value = int(item.value * 1.5)
            item.name = f"Superior {item.name}"
        elif quality == "masterwork" and hasattr(item, 'damage'):
            item.damage = int(item.damage * 1.5)
            item.value = int(item.value * 2)
            item.name = f"Masterwork {item.name}"

        return item

    def _enchant_weapon(self, weapon: Weapon, level: int) -> Weapon:
        """
        Apply random enchantment to weapon (Decorator pattern).

        Args:
            weapon: Weapon to enchant
            level: Enchantment level

        Returns:
            Enchanted weapon
        """
        enchantments = []

        if level >= 3:
            enchantments.append(FlamingWeapon)
            enchantments.append(FrostWeapon)

        if level >= 6:
            enchantments.append(VampiricWeapon)

        if level >= 10:
            # Can create legendary weapon
            return LegendaryWeapon(weapon, f"Legendary {weapon.name}")

        if enchantments:
            enchantment_class = random.choice(enchantments)
            return enchantment_class(weapon)

        return weapon

    def create_random_item(self, level: int = 1) -> Item:
        """
        Create random item appropriate for level.

        Args:
            level: Difficulty level

        Returns:
            Random item
        """
        # Weighted selection based on level
        if level <= 3:
            item_types = [ItemType.POTION] * 4 + \
                [ItemType.SWORD] * 2 + [ItemType.SHIELD]
        elif level <= 7:
            item_types = [ItemType.POTION] * 2 + [ItemType.SWORD] * \
                2 + [ItemType.SHIELD] * 2 + [ItemType.KEY]
        else:
            item_types = [ItemType.SWORD] * 3 + [ItemType.SHIELD] * \
                2 + [ItemType.POTION] + [ItemType.KEY]

        item_type = random.choice(item_types)

        # Random quality
        quality_roll = random.random()
        if quality_roll < 0.7:
            quality = "normal"
        elif quality_roll < 0.9:
            quality = "superior"
        else:
            quality = "masterwork"

        # Random enchantment chance increases with level
        enchanted = random.random() < (0.1 + level * 0.02)

        return self.create(
            item_type=item_type,
            level=level,
            quality=quality,
            enchanted=enchanted
        )

    def create_treasure_chest(self, level: int = 1) -> List[Item]:
        """
        Create contents for a treasure chest.

        Args:
            level: Chest level

        Returns:
            List of items
        """
        num_items = random.randint(1, 3 + level // 3)
        items = []

        for _ in range(num_items):
            items.append(self.create_random_item(level))

        # Chance for gold (represented as valuable item)
        if random.random() < 0.5:
            gold = Item(
                name=f"Gold Coins ({random.randint(10, 50) * level})",
                item_type=ItemType.POTION,  # Using POTION type for consumables
                description="Shiny gold coins",
                value=random.randint(10, 50) * level
            )
            items.append(gold)

        return items


# ============= Inventory Visitor for Statistics =============

class InventoryStatsVisitor(IVisitor):
    """
    Visitor for calculating inventory statistics.
    Example of Visitor pattern usage.
    """

    def __init__(self):
        """Initialize visitor."""
        self.total_items = 0
        self.total_value = 0
        self.total_weight = 0
        self.item_counts = {}

    def visit_entity(self, entity: Any) -> Dict[str, Any]:
        """Not applicable for inventory stats."""
        return {}

    def visit_item(self, item: Item) -> Dict[str, Any]:
        """Visit and analyze item."""
        self.total_items += 1
        self.total_value += item.value
        self.total_weight += item.weight

        item_type = item.item_type.value
        self.item_counts[item_type] = self.item_counts.get(item_type, 0) + 1

        return {
            "name": item.name,
            "value": item.value,
            "weight": item.weight,
            "type": item_type
        }

    def visit_room(self, room: Any) -> Dict[str, Any]:
        """Not applicable for inventory stats."""
        return {}

    def get_statistics(self) -> Dict[str, Any]:
        """Get collected statistics."""
        return {
            "total_items": self.total_items,
            "total_value": self.total_value,
            "total_weight": self.total_weight,
            "item_counts": self.item_counts
        }


# ============= Factory Singleton Instance =============

def get_item_factory() -> ItemFactory:
    """
    Get singleton instance of item factory.

    Returns:
        Item factory instance
    """
    if not hasattr(get_item_factory, "_instance"):
        get_item_factory._instance = ItemFactory()
    return get_item_factory._instance
