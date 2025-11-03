"""
Dungeon Builder implementation using Builder pattern.
Creates dungeons with various layouts and configurations.
"""

from typing import List, Optional, Dict
import random
from abc import abstractmethod

from src.core.interfaces import IBuilder, Direction, Position, EntityType, ItemType
from src.dungeon.room import Room, Dungeon
from src.entities.factories import get_entity_factory
from src.items.inventory import get_item_factory


class DungeonBuilder(IBuilder):
    """
    Abstract Builder for creating dungeons.
    Builder pattern implementation.

    GRASP Patterns:
    - Creator: Builder creates dungeon components
    - Low Coupling: Builder isolates dungeon creation complexity
    """

    def __init__(self):
        """Initialize builder."""
        self.dungeon: Optional[Dungeon] = None
        self.entity_factory = get_entity_factory()
        self.item_factory = get_item_factory()

    @abstractmethod
    def create_layout(self) -> None:
        """Create dungeon layout (rooms and connections)."""
        pass

    @abstractmethod
    def populate_rooms(self) -> None:
        """Populate rooms with entities and items."""
        pass

    @abstractmethod
    def set_special_rooms(self) -> None:
        """Set special room types (treasure, boss, etc.)."""
        pass

    def reset(self) -> None:
        """Reset builder to initial state."""
        self.dungeon = Dungeon()

    def build(self) -> Dungeon:
        """
        Build dungeon using Template Method pattern.

        Returns:
            Complete dungeon
        """
        if not self.dungeon:
            self.reset()

        # Template method - steps for building dungeon
        self.create_layout()
        self.set_special_rooms()
        self.populate_rooms()
        self._finalize()

        result = self.dungeon
        self.dungeon = None  # Reset for next build
        return result

    def _finalize(self) -> None:
        """Finalize dungeon creation (hook method)."""
        # Ensure entrance and exit are set
        if self.dungeon.rooms and not self.dungeon.entrance:
            self.dungeon.entrance = self.dungeon.rooms[0]
            self.dungeon.current_room = self.dungeon.entrance

        if self.dungeon.rooms and not self.dungeon.exit:
            # Set last room as exit if not already set
            last_room = self.dungeon.rooms[-1]
            last_room.is_exit = True
            self.dungeon.exit = last_room


class SimpleDungeonBuilder(DungeonBuilder):
    """
    Concrete builder for simple linear dungeons.
    Good for beginners.
    """

    def __init__(self, size: int = 5):
        """
        Initialize simple dungeon builder.

        Args:
            size: Number of rooms
        """
        super().__init__()
        self.size = size

    def create_layout(self) -> None:
        """Create linear layout."""
        self.reset()

        # Create linear chain of rooms
        for i in range(self.size):
            room = Room(
                name=f"Chamber {i+1}",
                description=self._get_room_description(i),
                position=Position(i, 0)
            )

            self.dungeon.add(room)

            # Connect to previous room
            if i > 0:
                prev_room = self.dungeon.rooms[i-1]
                prev_room.add_connection(Direction.EAST, room)

    def populate_rooms(self) -> None:
        """Add enemies and items to rooms."""
        for i, room in enumerate(self.dungeon.rooms):
            if i == 0:
                # Entrance - no enemies
                room.add(self.item_factory.create_random_item(level=1))
            elif i == self.size - 1:
                # Exit room - boss
                boss = self.entity_factory.create(
                    EntityType.DRAGON,
                    name="Guardian Dragon",
                    level=5
                )
                room.add(boss)
            else:
                # Regular rooms
                if random.random() < 0.7:
                    # Add enemy
                    monster = self.entity_factory.create_random_monster(
                        difficulty=i)
                    room.add(monster)

                if random.random() < 0.5:
                    # Add item
                    item = self.item_factory.create_random_item(level=i)
                    room.add(item)

    def set_special_rooms(self) -> None:
        """Set room types."""
        for i, room in enumerate(self.dungeon.rooms):
            if i == 0:
                room.room_type = "safe"
            elif i == self.size - 1:
                room.room_type = "boss"
                room.is_exit = True
            elif random.random() < 0.3:
                room.room_type = "treasure"

    def _get_room_description(self, index: int) -> str:
        """Generate room description based on index."""
        descriptions = [
            "A damp stone chamber with moss-covered walls.",
            "A circular room with ancient symbols on the floor.",
            "A long hall with crumbling pillars.",
            "A small alcove with scattered bones.",
            "A grand chamber with a vaulted ceiling.",
            "A narrow passage with dripping water.",
            "A room filled with broken statues.",
            "A chamber with glowing crystals in the walls."
        ]
        return descriptions[index % len(descriptions)]


class GridDungeonBuilder(DungeonBuilder):
    """
    Concrete builder for grid-based dungeons.
    Creates more complex layouts.
    """

    def __init__(self, width: int = 4, height: int = 4):
        """
        Initialize grid dungeon builder.

        Args:
            width: Grid width
            height: Grid height
        """
        super().__init__()
        self.width = width
        self.height = height
        self.grid: Dict[Position, Room] = {}

    def create_layout(self) -> None:
        """Create grid layout with random connections."""
        self.reset()
        self.grid.clear()

        # Create rooms in grid
        room_count = 0
        for y in range(self.height):
            for x in range(self.width):
                # Random chance to skip room (creates more interesting layouts)
                if room_count > 0 and random.random() < 0.3:
                    continue

                position = Position(x, y)
                room = Room(
                    name=self._generate_room_name(),
                    description=self._generate_room_description(),
                    position=position
                )

                self.grid[position] = room
                self.dungeon.add(room)
                room_count += 1

        # Create connections between adjacent rooms
        for position, room in self.grid.items():
            self._create_connections(room, position)

        # Ensure connectivity using DFS
        self._ensure_connectivity()

    def _create_connections(self, room: Room, position: Position) -> None:
        """
        Create connections to adjacent rooms.

        Args:
            room: Current room
            position: Room position
        """
        directions = [
            (Direction.NORTH, Position(position.x, position.y - 1)),
            (Direction.SOUTH, Position(position.x, position.y + 1)),
            (Direction.EAST, Position(position.x + 1, position.y)),
            (Direction.WEST, Position(position.x - 1, position.y))
        ]

        for direction, adj_pos in directions:
            if adj_pos in self.grid:
                # Random chance to create connection
                if random.random() < 0.7:
                    adj_room = self.grid[adj_pos]

                    # Random chance for locked door
                    locked = random.random() < 0.1
                    key_required = "iron" if locked else None

                    # Only add if connection doesn't exist
                    if direction not in room.connections:
                        room.add_connection(
                            direction, adj_room, locked, key_required)

    def _ensure_connectivity(self) -> None:
        """Ensure all rooms are reachable from entrance."""
        if not self.dungeon.rooms:
            return

        # DFS to find connected rooms
        entrance = self.dungeon.rooms[0]
        visited = set()
        stack = [entrance]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)

            for connection in current.connections.values():
                if connection.target_room not in visited:
                    stack.append(connection.target_room)

        # Connect unvisited rooms
        unvisited = set(self.dungeon.rooms) - visited
        for room in unvisited:
            # Find nearest visited room and connect
            nearest = min(visited, key=lambda r: self._distance(
                r.position, room.position))

            # Determine direction
            dx = room.position.x - nearest.position.x
            dy = room.position.y - nearest.position.y

            if abs(dx) > abs(dy):
                direction = Direction.EAST if dx > 0 else Direction.WEST
            else:
                direction = Direction.SOUTH if dy > 0 else Direction.NORTH

            nearest.add_connection(direction, room)

    def _distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate Manhattan distance between positions."""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def populate_rooms(self) -> None:
        """Populate rooms with entities and items."""
        room_count = len(self.dungeon.rooms)

        for i, room in enumerate(self.dungeon.rooms):
            difficulty = 1 + (i * 5) // room_count

            if i == 0:
                # Entrance - safe room
                room.add(self.item_factory.create(ItemType.POTION, level=1))
                room.add(self.item_factory.create(ItemType.SWORD, level=1))
            elif room.is_exit:
                # Exit - boss room
                boss = self.entity_factory.create(
                    EntityType.DRAGON,
                    name="Dungeon Lord",
                    level=difficulty + 2
                )
                room.add(boss)

                # Boss treasure
                for _ in range(3):
                    room.add(self.item_factory.create_random_item(
                        level=difficulty + 2))
            else:
                # Regular rooms
                self._populate_regular_room(room, difficulty)

    def _populate_regular_room(self, room: Room, difficulty: int) -> None:
        """
        Populate regular room based on type and difficulty.

        Args:
            room: Room to populate
            difficulty: Difficulty level
        """
        if room.room_type == "treasure":
            # Treasure room - more items, possibly guarded
            if random.random() < 0.5:
                # Guarded treasure
                guard = self.entity_factory.create_random_monster(
                    difficulty + 1)
                room.add(guard)

            # Add treasure
            num_items = random.randint(2, 4)
            for _ in range(num_items):
                room.add(self.item_factory.create_random_item(
                    level=difficulty + 1))

        elif room.room_type == "trap":
            # Trap room - fewer enemies but trap damage
            if random.random() < 0.3:
                monster = self.entity_factory.create_random_monster(difficulty)
                room.add(monster)

        else:
            # Normal room
            if random.random() < 0.6:
                # Add enemy
                if random.random() < 0.2:
                    # Multiple enemies
                    num_enemies = random.randint(2, 3)
                    for _ in range(num_enemies):
                        monster = self.entity_factory.create_random_monster(
                            difficulty - 1)
                        room.add(monster)
                else:
                    # Single enemy
                    monster = self.entity_factory.create_random_monster(
                        difficulty)
                    room.add(monster)

            if random.random() < 0.4:
                # Add item
                room.add(self.item_factory.create_random_item(level=difficulty))

            if random.random() < 0.1:
                # Add key
                key = self.item_factory.create(ItemType.KEY, level=difficulty)
                room.add(key)

    def set_special_rooms(self) -> None:
        """Set special room types."""
        if not self.dungeon.rooms:
            return

        # First room is entrance/safe
        self.dungeon.rooms[0].room_type = "safe"

        # Last room or furthest from entrance is exit
        entrance = self.dungeon.rooms[0]
        furthest_room = max(
            self.dungeon.rooms,
            key=lambda r: self._distance(entrance.position, r.position)
        )
        furthest_room.is_exit = True
        furthest_room.room_type = "boss"
        self.dungeon.exit = furthest_room

        # Set other special rooms
        remaining_rooms = [r for r in self.dungeon.rooms
                           if r != self.dungeon.rooms[0] and r != furthest_room]

        if remaining_rooms:
            # Some treasure rooms
            num_treasure = min(len(remaining_rooms) // 3, 2)
            for _ in range(num_treasure):
                if remaining_rooms:
                    room = random.choice(remaining_rooms)
                    room.room_type = "treasure"
                    remaining_rooms.remove(room)

            # Some trap rooms
            num_traps = min(len(remaining_rooms) // 4, 2)
            for _ in range(num_traps):
                if remaining_rooms:
                    room = random.choice(remaining_rooms)
                    room.room_type = "trap"
                    remaining_rooms.remove(room)

    def _generate_room_name(self) -> str:
        """Generate random room name."""
        prefixes = ["Dark", "Ancient", "Forgotten",
                    "Cursed", "Hidden", "Sacred", "Ruined"]
        suffixes = ["Chamber", "Hall", "Sanctum",
                    "Vault", "Crypt", "Gallery", "Passage"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def _generate_room_description(self) -> str:
        """Generate random room description."""
        descriptions = [
            "Stone walls echo with distant sounds.",
            "Dust motes dance in shafts of pale light.",
            "The air is thick with ancient magic.",
            "Shadows move strangely in the corners.",
            "Water drips steadily from the ceiling.",
            "Old battle scars mark the walls.",
            "Strange runes glow faintly on the floor.",
            "The smell of decay hangs heavy here.",
            "Cobwebs shroud forgotten treasures.",
            "Cold wind whistles through unseen cracks."
        ]
        return random.choice(descriptions)


class ProceduralDungeonBuilder(GridDungeonBuilder):
    """
    Advanced builder using procedural generation algorithms.
    Creates organic, cave-like dungeons.
    """

    def __init__(self, width: int = 6, height: int = 6, complexity: float = 0.5):
        """
        Initialize procedural builder.

        Args:
            width: Grid width
            height: Grid height
            complexity: Dungeon complexity (0.0 - 1.0)
        """
        super().__init__(width, height)
        self.complexity = max(0.0, min(1.0, complexity))

    def create_layout(self) -> None:
        """Create organic layout using cellular automata."""
        self.reset()
        self.grid.clear()

        # Initialize grid with random cells
        initial_grid = self._initialize_random_grid()

        # Apply cellular automata rules
        iterations = int(3 + self.complexity * 3)
        for _ in range(iterations):
            initial_grid = self._apply_cellular_automata(initial_grid)

        # Convert to rooms
        self._convert_to_rooms(initial_grid)

        # Ensure connectivity
        self._ensure_connectivity()

        # Add some extra connections for variety
        self._add_extra_connections()

    def _initialize_random_grid(self) -> List[List[bool]]:
        """Initialize random grid for cellular automata."""
        grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Higher complexity = more initial rooms
                threshold = 0.3 + self.complexity * 0.3
                row.append(random.random() < threshold)
            grid.append(row)
        return grid

    def _apply_cellular_automata(self, grid: List[List[bool]]) -> List[List[bool]]:
        """Apply cellular automata rules to smooth the dungeon."""
        new_grid = []

        for y in range(self.height):
            new_row = []
            for x in range(self.width):
                neighbors = self._count_neighbors(grid, x, y)

                # Cellular automata rule
                if grid[y][x]:
                    # Room exists - keep if enough neighbors
                    new_row.append(neighbors >= 3)
                else:
                    # No room - create if many neighbors
                    new_row.append(neighbors >= 5)

            new_grid.append(new_row)

        return new_grid

    def _count_neighbors(self, grid: List[List[bool]], x: int, y: int) -> int:
        """Count neighbors in 8 directions."""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if grid[ny][nx]:
                        count += 1
        return count

    def _convert_to_rooms(self, grid: List[List[bool]]) -> None:
        """Convert boolean grid to rooms."""
        for y in range(self.height):
            for x in range(self.width):
                if grid[y][x]:
                    position = Position(x, y)
                    room = Room(
                        name=self._generate_room_name(),
                        description=self._generate_procedural_description(
                            x, y),
                        position=position
                    )

                    self.grid[position] = room
                    self.dungeon.add(room)

        # Create basic connections
        for position, room in self.grid.items():
            self._create_connections(room, position)

    def _add_extra_connections(self) -> None:
        """Add extra connections for more interesting gameplay."""
        for room in self.dungeon.rooms:
            # Chance for secret passage
            if random.random() < 0.1 * self.complexity:
                possible_targets = [
                    r for r in self.dungeon.rooms
                    if r != room and self._distance(r.position, room.position) > 2
                ]

                if possible_targets:
                    target = random.choice(possible_targets)
                    # Create hidden connection
                    direction = random.choice(list(Direction))
                    if direction not in room.connections:
                        room.add_connection(direction, target)
                        room.connections[direction].hidden = True

    def _generate_procedural_description(self, x: int, y: int) -> str:
        """Generate description based on position."""
        # Use position as seed for consistent descriptions
        seed = x * 100 + y
        random.seed(seed)

        description = super()._generate_room_description()

        # Add procedural details
        if x == 0 or x == self.width - 1:
            description += " The walls here feel particularly cold."
        if y == 0 or y == self.height - 1:
            description += " You sense you're near the dungeon's edge."

        random.seed()  # Reset random seed
        return description


# ============= Director Class (Optional) =============

class DungeonDirector:
    """
    Director class for coordinating builders.
    Part of Builder pattern.
    """

    def __init__(self):
        """Initialize director."""
        self.builder: Optional[DungeonBuilder] = None

    def set_builder(self, builder: DungeonBuilder) -> None:
        """Set the builder to use."""
        self.builder = builder

    def construct_beginner_dungeon(self) -> Dungeon:
        """Construct a beginner-friendly dungeon."""
        self.builder = SimpleDungeonBuilder(size=5)
        return self.builder.build()

    def construct_intermediate_dungeon(self) -> Dungeon:
        """Construct an intermediate dungeon."""
        self.builder = GridDungeonBuilder(width=4, height=4)
        return self.builder.build()

    def construct_advanced_dungeon(self) -> Dungeon:
        """Construct an advanced dungeon."""
        self.builder = ProceduralDungeonBuilder(
            width=6, height=6, complexity=0.7)
        return self.builder.build()

    def construct_custom_dungeon(self, builder: DungeonBuilder) -> Dungeon:
        """Construct dungeon with custom builder."""
        self.builder = builder
        return self.builder.build()
