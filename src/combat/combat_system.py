"""
Combat system implementation using Strategy and Template Method patterns.
Manages turn-based combat between entities.
"""

from typing import Optional, Dict, Any, List
from abc import abstractmethod
import random

from src.core.interfaces import ICombatStrategy, ICombatant
from src.core.event_system import EventSystem, GameEvents
from src.entities.base import Entity


class CombatStrategy(ICombatStrategy):
    """
    Base combat strategy implementation.
    Strategy pattern for different combat approaches.
    """

    @abstractmethod
    def calculate_damage(self, attacker: ICombatant, defender: ICombatant) -> int:
        """Calculate damage for attack."""
        pass

    @abstractmethod
    def calculate_hit_chance(self, attacker: ICombatant, defender: ICombatant) -> float:
        """Calculate chance to hit."""
        pass

    def execute_turn(self, attacker: ICombatant, defender: ICombatant) -> Dict[str, Any]:
        """
        Execute combat turn.

        Args:
            attacker: Attacking entity
            defender: Defending entity

        Returns:
            Turn results
        """
        results = {
            "attacker": attacker,
            "defender": defender,
            "hit": False,
            "damage": 0,
            "critical": False,
            "dodged": False
        }

        # Check hit chance
        hit_chance = self.calculate_hit_chance(attacker, defender)
        if random.random() > hit_chance:
            results["dodged"] = True
            return results

        # Calculate damage
        damage = self.calculate_damage(attacker, defender)

        # Check for critical hit
        if random.random() < self.get_critical_chance(attacker):
            damage = int(damage * 1.5)
            results["critical"] = True

        # Apply damage
        defender.take_damage(damage)

        results["hit"] = True
        results["damage"] = damage

        return results

    def get_critical_chance(self, attacker: ICombatant) -> float:
        """Get critical hit chance."""
        return 0.1  # 10% base critical chance

    @abstractmethod
    def get_description(self) -> str:
        """Get strategy description."""
        pass


class AggressiveStrategy(CombatStrategy):
    """
    Aggressive combat strategy - high damage, low defense.
    """

    def calculate_damage(self, attacker: ICombatant, defender: ICombatant) -> int:
        """Calculate increased damage."""
        base_damage = attacker.calculate_damage()
        # 20% damage bonus
        return int(base_damage * 1.2)

    def calculate_hit_chance(self, attacker: ICombatant, defender: ICombatant) -> float:
        """Standard hit chance."""
        return 0.85

    def get_critical_chance(self, attacker: ICombatant) -> float:
        """Higher critical chance."""
        return 0.15

    def get_description(self) -> str:
        """Get strategy description."""
        return "Aggressive: +20% damage, +5% critical chance"


class DefensiveStrategy(CombatStrategy):
    """
    Defensive combat strategy - lower damage, better survivability.
    """

    def calculate_damage(self, attacker: ICombatant, defender: ICombatant) -> int:
        """Calculate reduced damage."""
        base_damage = attacker.calculate_damage()
        # 20% damage penalty
        return int(base_damage * 0.8)

    def calculate_hit_chance(self, attacker: ICombatant, defender: ICombatant) -> float:
        """Higher hit chance due to careful attacks."""
        return 0.95

    def get_description(self) -> str:
        """Get strategy description."""
        return "Defensive: -20% damage, +10% hit chance, reduces incoming damage"

    def execute_turn(self, attacker: ICombatant, defender: ICombatant) -> Dict[str, Any]:
        """Execute defensive turn with counter chance."""
        results = super().execute_turn(attacker, defender)

        # Chance to reduce incoming damage on next turn
        if results["hit"] and isinstance(attacker, Entity):
            attacker.apply_status_effect("defensive_stance", 1)

        return results


class BalancedStrategy(CombatStrategy):
    """
    Balanced combat strategy - standard combat approach.
    """

    def calculate_damage(self, attacker: ICombatant, defender: ICombatant) -> int:
        """Calculate standard damage."""
        return attacker.calculate_damage()

    def calculate_hit_chance(self, attacker: ICombatant, defender: ICombatant) -> float:
        """Standard hit chance."""
        return 0.9

    def get_description(self) -> str:
        """Get strategy description."""
        return "Balanced: Standard combat with no modifiers"


class BerserkStrategy(CombatStrategy):
    """
    Berserk strategy - extreme damage at the cost of defense.
    """

    def calculate_damage(self, attacker: ICombatant, defender: ICombatant) -> int:
        """Calculate massive damage."""
        base_damage = attacker.calculate_damage()
        # 50% damage bonus
        return int(base_damage * 1.5)

    def calculate_hit_chance(self, attacker: ICombatant, defender: ICombatant) -> float:
        """Lower hit chance due to reckless attacks."""
        return 0.7

    def get_critical_chance(self, attacker: ICombatant) -> float:
        """Very high critical chance."""
        return 0.25

    def execute_turn(self, attacker: ICombatant, defender: ICombatant) -> Dict[str, Any]:
        """Execute berserk attack with self-damage risk."""
        results = super().execute_turn(attacker, defender)

        # Risk of self-damage
        if random.random() < 0.1:
            self_damage = int(attacker.calculate_damage() * 0.1)
            attacker.take_damage(self_damage)
            results["self_damage"] = self_damage

        return results

    def get_description(self) -> str:
        """Get strategy description."""
        return "Berserk: +50% damage, +15% critical, but risky"


class CombatSystem:
    """
    Main combat system using Template Method pattern.
    Manages turn-based combat encounters.

    GRASP Patterns:
    - Controller: Controls combat flow
    - Information Expert: Knows about combat rules
    """

    def __init__(self):
        """Initialize combat system."""
        self.event_system = EventSystem()
        self.combat_log: List[str] = []
        self.turn_count = 0
        self.is_active = False
        self.participants: List[ICombatant] = []
        self.current_strategy: ICombatStrategy = BalancedStrategy()

    def set_strategy(self, strategy: ICombatStrategy) -> None:
        """
        Set combat strategy.

        Args:
            strategy: Combat strategy to use
        """
        self.current_strategy = strategy
        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": f"Combat strategy changed to: {strategy.get_description()}",
            "type": "combat_info"
        })

    def start_combat(self, participants: List[ICombatant]) -> None:
        """
        Start combat encounter (Template Method).

        Args:
            participants: List of combat participants
        """
        self.is_active = True
        self.participants = participants
        self.turn_count = 0
        self.combat_log.clear()

        # Notify combat start
        self.event_system.notify(GameEvents.COMBAT_STARTED, {
            "participants": participants
        })

        self._log_message("⚔️ Combat begins!")

        # Show participants
        for participant in participants:
            if isinstance(participant, Entity):
                self._log_message(
                    f"  • {participant.name}: {participant.stats}")

    def execute_round(self) -> bool:
        """
        Execute one round of combat.
        Template Method pattern - defines combat round structure.

        Returns:
            True if combat continues, False if ended
        """
        if not self.is_active:
            return False

        self.turn_count += 1
        self._log_message(f"\n--- Round {self.turn_count} ---")

        # Phase 1: Preparation
        self._preparation_phase()

        # Phase 2: Action resolution
        combat_ended = self._action_phase()

        # Phase 3: End of round
        self._end_round_phase()

        if combat_ended:
            self.end_combat()
            return False

        return True

    def _preparation_phase(self) -> None:
        """Preparation phase - status effects, buffs, etc."""
        for participant in self.participants:
            if isinstance(participant, Entity) and participant.is_alive():
                # Trigger turn start behaviors
                participant.behavior.on_turn_start(participant)

                # Update status effects
                participant.update_status_effects()

    def _action_phase(self) -> bool:
        """
        Action resolution phase.

        Returns:
            True if combat should end
        """
        # Get living participants
        living = [p for p in self.participants if p.is_alive()]

        if len(living) <= 1:
            return True

        # Determine turn order (could be enhanced with speed stat)
        turn_order = self._determine_turn_order(living)

        for attacker in turn_order:
            if not attacker.is_alive():
                continue

            # Find valid targets
            targets = [p for p in living if p != attacker and p.is_alive()]
            if not targets:
                return True

            # Execute action
            self._execute_entity_action(attacker, targets)

        return False

    def _execute_entity_action(self, entity: ICombatant, targets: List[ICombatant]) -> None:
        """
        Execute entity's combat action.

        Args:
            entity: Acting entity
            targets: Available targets
        """
        # For NPCs, use AI behavior
        if isinstance(entity, Entity) and entity.behavior:
            context = {
                "player_in_range": True,
                "targets": targets,
                "turn": self.turn_count
            }
            action = entity.behavior.get_action(entity, context)

            if action == "attack" and targets:
                target = random.choice(targets)
                self.execute_attack(entity, target)
            elif action == "defend":
                entity.defend()
                self._log_message(f"{entity.name} takes a defensive stance!")
            elif action == "flee":
                self._log_message(f"{entity.name} tries to flee!")
                # Could implement flee logic
            else:
                self._log_message(f"{entity.name} waits...")

    def execute_attack(self, attacker: ICombatant, defender: ICombatant) -> Dict[str, Any]:
        """
        Execute attack using current strategy.

        Args:
            attacker: Attacking entity
            defender: Defending entity

        Returns:
            Attack results
        """
        results = self.current_strategy.execute_turn(attacker, defender)

        # Log attack results
        if results["dodged"]:
            self._log_message(f"❌ {attacker.name} misses {defender.name}!")
        elif results["critical"]:
            self._log_message(
                f"💥 CRITICAL HIT! {attacker.name} deals {results['damage']} damage to {defender.name}!")
        else:
            self._log_message(
                f"⚔️ {attacker.name} deals {results['damage']} damage to {defender.name}!")

        if "self_damage" in results:
            self._log_message(
                f"💢 {attacker.name} hurts themselves for {results['self_damage']} damage!")

        # Check if defender died
        if not defender.is_alive():
            self._log_message(f"☠️ {defender.name} has been defeated!")

        # Notify about combat turn
        self.event_system.notify(GameEvents.COMBAT_TURN, results)

        return results

    def _end_round_phase(self) -> None:
        """End of round phase - cleanup, regeneration, etc."""
        # Could implement end-of-round effects here
        pass

    def _determine_turn_order(self, participants: List[ICombatant]) -> List[ICombatant]:
        """
        Determine turn order for participants.
        Could be enhanced with initiative/speed stats.

        Args:
            participants: Combat participants

        Returns:
            Ordered list of participants
        """
        # For now, random order with player going first
        from src.core.interfaces import EntityType

        players = []
        others = []

        for p in participants:
            if isinstance(p, Entity) and p.entity_type == EntityType.PLAYER:
                players.append(p)
            else:
                others.append(p)

        random.shuffle(others)
        return players + others

    def end_combat(self) -> None:
        """End combat encounter."""
        if not self.is_active:
            return

        self.is_active = False

        # Determine winner
        living = [p for p in self.participants if p.is_alive()]

        if living:
            self._log_message(f"\n🏆 Combat ended! Victor: {living[0].name}")
        else:
            self._log_message("\n💀 Combat ended with no survivors!")

        # Notify combat end
        self.event_system.notify(GameEvents.COMBAT_ENDED, {
            "participants": self.participants,
            "survivors": living,
            "turns": self.turn_count
        })

        self.participants.clear()

    def _log_message(self, message: str) -> None:
        """
        Log combat message.

        Args:
            message: Message to log
        """
        self.combat_log.append(message)
        self.event_system.notify(GameEvents.UI_MESSAGE, {
            "message": message,
            "type": "combat"
        })

    def get_combat_log(self) -> List[str]:
        """Get combat log."""
        return self.combat_log.copy()

    def is_combat_active(self) -> bool:
        """Check if combat is active."""
        return self.is_active


# ============= Combat Manager Singleton =============

_combat_system_instance: Optional[CombatSystem] = None


def get_combat_system() -> CombatSystem:
    """
    Get singleton instance of combat system.

    Returns:
        Combat system instance
    """
    global _combat_system_instance
    if _combat_system_instance is None:
        _combat_system_instance = CombatSystem()
    return _combat_system_instance
