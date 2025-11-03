"""
Item system with Decorator pattern for enhancements.
Items can be decorated with various enchantments and modifiers.
"""

from typing import Dict, Any
import copy

from src.core.interfaces import (
    IComponent, IDecorator, IVisitable, IVisitor,
    ItemType, IPrototype
)
from src.core.event_system import EventSystem, GameEvents


class Item(IComponent, IVisitable, IPrototype):
    """
    Base Item class.

    Design Patterns:
    - Component: Part of Composite pattern for inventory
    - Visitor: Can be inspected
    - Prototype: Can be cloned
    """

    def __init__(
        self,
        name: str,
        item_type: ItemType,
        description: str,
        value: int = 0,
        weight: int = 1
    ):
        """
        Initialize item.

        Args:
            name: Item name
            item_type: Type of item
            description: Item description
            value: Item value in gold
            weight: Item weight
        """
        self.name = name
        self.item_type = item_type
        self.description = description
        self.value = value
        self.weight = weight
        self.equipped = False

    def get_name(self) -> str:
        """Get item name."""
        return self.name

    def get_description(self) -> str:
        """Get item description."""
        return self.description

    def use(self, user: Any) -> bool:
        """
        Use item. Override in subclasses.

        Args:
            user: Entity using the item

        Returns:
            True if item was used successfully
        """
        return False

    def equip(self, user: Any) -> bool:
        """
        Equip item. Override in equipment subclasses.

        Args:
            user: Entity equipping the item

        Returns:
            True if equipped successfully
        """
        return False

    def unequip(self, user: Any) -> bool:
        """
        Unequip item.

        Args:
            user: Entity unequipping the item

        Returns:
            True if unequipped successfully
        """
        self.equipped = False
        return True

    def accept(self, visitor: IVisitor) -> Any:
        """Accept visitor for inspection."""
        return visitor.visit_item(self)

    def clone(self) -> 'Item':
        """Create a copy of this item."""
        return copy.deepcopy(self)

    def get_stats_modifier(self) -> Dict[str, int]:
        """
        Get stats modifications provided by item.
        Override in equipment subclasses.

        Returns:
            Dictionary of stat modifications
        """
        return {}

    def __str__(self) -> str:
        """String representation."""
        equipped_str = " [E]" if self.equipped else ""
        return f"{self.name}{equipped_str} - {self.description}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Item(name='{self.name}', type={self.item_type}, value={self.value})"


# ============= Concrete Items =============

class Weapon(Item):
    """Base weapon class."""

    def __init__(
        self,
        name: str,
        description: str,
        damage: int,
        value: int = 0
    ):
        """
        Initialize weapon.

        Args:
            name: Weapon name
            description: Weapon description
            damage: Base damage
            value: Weapon value
        """
        super().__init__(name, ItemType.SWORD, description, value, weight=5)
        self.damage = damage

    def get_stats_modifier(self) -> Dict[str, int]:
        """Get attack bonus from weapon."""
        return {"attack": self.damage}

    def equip(self, user: Any) -> bool:
        """Equip weapon."""
        if not self.equipped:
            self.equipped = True
            user.stats.attack += self.damage

            EventSystem().notify(GameEvents.ITEM_EQUIPPED, {
                "item": self,
                "user": user
            })
            return True
        return False

    def unequip(self, user: Any) -> bool:
        """Unequip weapon."""
        if self.equipped:
            self.equipped = False
            user.stats.attack -= self.damage

            EventSystem().notify(GameEvents.ITEM_UNEQUIPPED, {
                "item": self,
                "user": user
            })
            return True
        return False

    def get_description(self) -> str:
        """Get weapon description with damage."""
        return f"{self.description} (Damage: +{self.damage})"


class Shield(Item):
    """Shield item for defense."""

    def __init__(
        self,
        name: str,
        description: str,
        defense: int,
        value: int = 0
    ):
        """
        Initialize shield.

        Args:
            name: Shield name
            description: Shield description
            defense: Defense bonus
            value: Shield value
        """
        super().__init__(name, ItemType.SHIELD, description, value, weight=7)
        self.defense = defense

    def get_stats_modifier(self) -> Dict[str, int]:
        """Get defense bonus from shield."""
        return {"defense": self.defense}

    def equip(self, user: Any) -> bool:
        """Equip shield."""
        if not self.equipped:
            self.equipped = True
            user.stats.defense += self.defense

            EventSystem().notify(GameEvents.ITEM_EQUIPPED, {
                "item": self,
                "user": user
            })
            return True
        return False

    def unequip(self, user: Any) -> bool:
        """Unequip shield."""
        if self.equipped:
            self.equipped = False
            user.stats.defense -= self.defense

            EventSystem().notify(GameEvents.ITEM_UNEQUIPPED, {
                "item": self,
                "user": user
            })
            return True
        return False

    def get_description(self) -> str:
        """Get shield description with defense."""
        return f"{self.description} (Defense: +{self.defense})"


class Potion(Item):
    """Consumable healing potion."""

    def __init__(
        self,
        name: str = "Health Potion",
        description: str = "Restores health",
        healing: int = 50,
        value: int = 25
    ):
        """
        Initialize potion.

        Args:
            name: Potion name
            description: Potion description
            healing: Healing amount
            value: Potion value
        """
        super().__init__(name, ItemType.POTION, description, value, weight=1)
        self.healing = healing
        self.consumed = False

    def use(self, user: Any) -> bool:
        """
        Use potion to heal.

        Args:
            user: Entity using the potion

        Returns:
            True if used successfully
        """
        if not self.consumed:
            user.heal(self.healing)
            self.consumed = True

            EventSystem().notify(GameEvents.ITEM_USED, {
                "item": self,
                "user": user,
                "effect": f"Healed {self.healing} HP"
            })
            return True
        return False

    def get_description(self) -> str:
        """Get potion description with healing amount."""
        return f"{self.description} (Heals: {self.healing} HP)"


class Key(Item):
    """Key item for unlocking doors."""

    def __init__(
        self,
        name: str = "Key",
        description: str = "Opens locked doors",
        key_id: str = "default"
    ):
        """
        Initialize key.

        Args:
            name: Key name
            description: Key description
            key_id: Unique key identifier
        """
        super().__init__(name, ItemType.KEY, description, value=0, weight=0)
        self.key_id = key_id

    def use(self, user: Any, target: Any = None) -> bool:
        """
        Use key on a lock.

        Args:
            user: Entity using the key
            target: Lock to open

        Returns:
            True if used successfully
        """
        if target and hasattr(target, 'unlock'):
            if target.unlock(self.key_id):
                EventSystem().notify(GameEvents.ITEM_USED, {
                    "item": self,
                    "user": user,
                    "effect": "Unlocked door"
                })
                return True
        return False


# ============= Decorator Pattern for Weapon Enhancements =============

class WeaponDecorator(Weapon, IDecorator):
    """
    Base decorator for weapon enhancements.
    Decorator pattern implementation.
    """

    def __init__(self, weapon: Weapon):
        """
        Initialize decorator.

        Args:
            weapon: Weapon to decorate
        """
        self._wrapped_weapon = weapon
        super().__init__(
            name=weapon.name,
            description=weapon.description,
            damage=weapon.damage,
            value=weapon.value
        )

    def get_wrapped(self) -> IComponent:
        """Get wrapped weapon."""
        return self._wrapped_weapon

    def get_name(self) -> str:
        """Get decorated name."""
        return self._wrapped_weapon.get_name()

    def get_description(self) -> str:
        """Get decorated description."""
        return self._wrapped_weapon.get_description()

    def get_stats_modifier(self) -> Dict[str, int]:
        """Get combined stats modifier."""
        return self._wrapped_weapon.get_stats_modifier()

    @property
    def damage(self) -> int:
        """Get total damage including decorations."""
        if isinstance(self._wrapped_weapon, WeaponDecorator):
            return self._wrapped_weapon.damage
        return self._wrapped_weapon.damage


class FlamingWeapon(WeaponDecorator):
    """Flaming weapon enchantment."""

    def __init__(self, weapon: Weapon):
        """Add fire enchantment to weapon."""
        super().__init__(weapon)
        self.fire_damage = 5

    def get_name(self) -> str:
        """Add 'Flaming' prefix."""
        return f"Flaming {self._wrapped_weapon.get_name()}"

    def get_description(self) -> str:
        """Add fire damage description."""
        base_desc = self._wrapped_weapon.get_description()
        return f"{base_desc} [Fire: +{self.fire_damage}]"

    def get_stats_modifier(self) -> Dict[str, int]:
        """Add fire damage to attack."""
        stats = super().get_stats_modifier()
        stats["attack"] = stats.get("attack", 0) + self.fire_damage
        return stats

    @property
    def damage(self) -> int:
        """Get total damage including fire."""
        return super().damage + self.fire_damage


class FrostWeapon(WeaponDecorator):
    """Frost weapon enchantment."""

    def __init__(self, weapon: Weapon):
        """Add frost enchantment to weapon."""
        super().__init__(weapon)
        self.frost_damage = 3
        self.slow_chance = 0.3

    def get_name(self) -> str:
        """Add 'Frost' prefix."""
        return f"Frost {self._wrapped_weapon.get_name()}"

    def get_description(self) -> str:
        """Add frost effect description."""
        base_desc = self._wrapped_weapon.get_description()
        return f"{base_desc} [Frost: +{self.frost_damage}, {int(self.slow_chance*100)}% slow]"

    def get_stats_modifier(self) -> Dict[str, int]:
        """Add frost damage to attack."""
        stats = super().get_stats_modifier()
        stats["attack"] = stats.get("attack", 0) + self.frost_damage
        return stats

    @property
    def damage(self) -> int:
        """Get total damage including frost."""
        return super().damage + self.frost_damage


class VampiricWeapon(WeaponDecorator):
    """Vampiric weapon that heals on hit."""

    def __init__(self, weapon: Weapon):
        """Add vampiric enchantment to weapon."""
        super().__init__(weapon)
        self.lifesteal = 0.2  # 20% lifesteal

    def get_name(self) -> str:
        """Add 'Vampiric' prefix."""
        return f"Vampiric {self._wrapped_weapon.get_name()}"

    def get_description(self) -> str:
        """Add lifesteal description."""
        base_desc = self._wrapped_weapon.get_description()
        return f"{base_desc} [Lifesteal: {int(self.lifesteal*100)}%]"


class LegendaryWeapon(WeaponDecorator):
    """Legendary weapon with multiple enhancements."""

    def __init__(self, weapon: Weapon, legendary_name: str = "Excalibur"):
        """Create legendary weapon."""
        super().__init__(weapon)
        self.legendary_name = legendary_name
        self.bonus_damage = 10
        self.bonus_stats = {
            "health": 20,
            "defense": 5
        }

    def get_name(self) -> str:
        """Get legendary name."""
        return self.legendary_name

    def get_description(self) -> str:
        """Get legendary description."""
        return f"Legendary weapon of immense power! [Damage: +{self.damage}, " \
               f"Health: +{self.bonus_stats['health']}, Defense: +{self.bonus_stats['defense']}]"

    def get_stats_modifier(self) -> Dict[str, int]:
        """Get all legendary bonuses."""
        stats = super().get_stats_modifier()
        stats["attack"] = stats.get("attack", 0) + self.bonus_damage
        stats.update(self.bonus_stats)
        return stats

    @property
    def damage(self) -> int:
        """Get total legendary damage."""
        return super().damage + self.bonus_damage
