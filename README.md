# 🎮 Dungeon Crawler - Design Patterns Implementation

## 📝 Курсова робота: Консольна гра з використанням патернів проектування

### Опис проекту
Це текстова RPG-гра "Dungeon Crawler", розроблена для демонстрації різних патернів проектування. Гравець досліджує підземелля, б'ється з монстрами, збирає предмети та намагається знайти вихід.

## 🚀 Як запустити

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Запустити гру
python main.py

# 3. Запустити демонстрацію патернів
python test_patterns.py
```

## 🏗️ Реалізовані патерни проектування

### ✨ Породжувальні патерни (Creational Patterns)

#### 1. **Abstract Factory** (`src/entities/factories.py`)
```python
EntityFactory - створює різні типи істот (гравця, монстрів)
ItemFactory - створює різні типи предметів
```
- Використання: Створення сімейств пов'язаних об'єктів
- Приклад: `MonsterFactory`, `BossFactory` для спеціалізованого створення

#### 2. **Builder** (`src/dungeon/builders.py`)
```python
DungeonBuilder - абстрактний будівельник
SimpleDungeonBuilder - лінійні підземелля
GridDungeonBuilder - сіткові підземелля
ProceduralDungeonBuilder - процедурна генерація
```
- Використання: Покрокове створення складних підземель
- Директор: `DungeonDirector` координує процес побудови

#### 3. **Singleton** (`src/core/event_system.py`, `src/core/game_engine.py`)
```python
EventSystem - єдина система подій
GameEngine - єдиний ігровий движок
```
- Використання: Глобальний доступ до критичних систем

#### 4. **Prototype** (`src/entities/base.py`)
```python
Entity.clone() - клонування істот
Item.clone() - клонування предметів
```
- Використання: Ефективне створення схожих об'єктів

### 🔧 Структурні патерни (Structural Patterns)

#### 5. **Bridge** (`src/entities/base.py`)
```python
Entity (абстракція) <-> EntityBehavior (реалізація)
```
- Розділяє істоту від її поведінки
- Приклади поведінок: `AggressiveBehavior`, `DefensiveBehavior`

#### 6. **Composite** (`src/dungeon/room.py`, `src/items/inventory.py`)
```python
Dungeon -> Room -> [Entity, Item]
Inventory -> [Item, SubInventory]
```
- Використання: Ієрархічна структура підземелля та інвентаря

#### 7. **Decorator** (`src/items/items.py`)
```python
Weapon -> FlamingWeapon -> FrostWeapon -> VampiricWeapon
```
- Динамічне додавання властивостей зброї
- Приклад: `FlamingWeapon(FrostWeapon(sword))`

#### 8. **Facade** (`src/core/game_engine.py`)
```python
GameEngine - спрощений інтерфейс до всіх підсистем
```
- Приховує складність взаємодії компонентів

#### 9. **Adapter** (`src/ui/console_ui.py`)
```python
ConsoleAdapter - адаптує UI для різних виводів
```
- Можна розширити для GUI або веб-інтерфейсу

### 🎯 Поведінкові патерни (Behavioral Patterns)

#### 10. **Strategy** (`src/combat/combat_system.py`)
```python
CombatStrategy:
- AggressiveStrategy (+20% damage)
- DefensiveStrategy (-20% damage, +10% hit)
- BalancedStrategy (standard)
- BerserkStrategy (+50% damage, risky)
```
- Динамічна зміна стратегії бою

#### 11. **Observer** (`src/core/event_system.py`)
```python
EventSystem - Subject
Observers:
- AchievementObserver (відстежує досягнення)
- LoggingObserver (логує події)
```
- Використання: Система подій для loose coupling

#### 12. **Command** (`src/ui/commands.py`)
```python
Commands:
- MoveCommand
- AttackCommand
- TakeCommand
- UseCommand
```
- Інкапсуляція дій з можливістю undo

#### 13. **State** (`src/core/game_state.py`)
```python
GameStates:
- MenuState
- ExploringState
- CombatState
- InventoryState
- GameOverState
```
- Керування станами гри

#### 14. **Chain of Responsibility** (`src/ui/commands.py`)
```python
CommandHandler chain:
MovementHandler -> CombatHandler -> ItemHandler -> InformationHandler
```
- Обробка команд через ланцюжок

#### 15. **Template Method** (`src/combat/combat_system.py`)
```python
CombatSystem.execute_round():
1. _preparation_phase()
2. _action_phase()
3. _end_round_phase()
```
- Визначає скелет алгоритму бою

#### 16. **Visitor** (`src/items/inventory.py`)
```python
InventoryStatsVisitor - збирає статистику інвентаря
```
- Відвідує items та rooms для аналізу

#### 17. **Memento** (`src/core/game_state.py`)
```python
GameMemento - зберігає стан гри
SaveGameManager - Caretaker
```
- Система збереження/завантаження гри

## 🎯 SOLID принципи

### **S** - Single Responsibility
- Кожен клас має одну відповідальність
- Приклад: `Room` - тільки логіка кімнати

### **O** - Open/Closed
- Відкриті для розширення через наслідування
- Приклад: Нові типи монстрів через `EntityFactory`

### **L** - Liskov Substitution
- Підкласи взаємозамінні з базовими
- Приклад: Всі `Entity` працюють однаково

### **I** - Interface Segregation
- Багато специфічних інтерфейсів
- Приклад: `IDamageable`, `IAttacker`, `ICombatant`

### **D** - Dependency Inversion
- Залежності через абстракції
- Приклад: `GameEngine` залежить від інтерфейсів

## 📊 GRASP патерни

### Information Expert
- `Entity` знає свої характеристики
- `Room` знає свій вміст

### Creator
- `EntityFactory` створює entities
- `DungeonBuilder` створює dungeons

### Controller
- `GameEngine` - головний контролер
- `CombatSystem` - контролер бою

### Low Coupling
- Компоненти незалежні через інтерфейси
- EventSystem для непрямої комунікації

### High Cohesion
- Модулі мають чітку відповідальність
- Приклад: всі combat класи в одному модулі

### Polymorphism
- Різні типи `Entity` з різною поведінкою
- Різні `CombatStrategy` реалізації

### Pure Fabrication
- `EventSystem` - службовий клас
- `ConsoleUI` - не domain концепт

### Indirection
- `EventSystem` як посередник
- Інтерфейси для непрямої взаємодії

### Protected Variations
- Інтерфейси захищають від змін
- Factory ізолює створення об'єктів

## 🎮 Геймплей

### Команди гри:
- **Рух**: `move north/south/east/west` (або n/s/e/w)
- **Бій**: `attack`, `defend`, `flee`
- **Предмети**: `take <item>`, `use <item>`, `equip <item>`
- **Інформація**: `look`, `inventory`, `stats`
- **Система**: `save`, `load`, `quit`

### Типи кімнат:
- **Normal** - звичайні кімнати
- **Treasure** - скарбниці з цінними предметами
- **Boss** - кімната з босом
- **Trap** - кімнати з пастками
- **Safe** - безпечні кімнати (вхід)

### Типи ворогів:
- **Goblin** - слабкий, агресивний
- **Skeleton** - збалансований, захисний
- **Dragon** - бос, дуже сильний

### Предмети:
- **Weapons** - мечі з різними зачаруваннями
- **Shields** - щити для захисту
- **Potions** - зілля лікування
- **Keys** - ключі для замкнених дверей

## 📁 Структура проекту

```
dungeon_crawler/
├── main.py                    # Точка входу
├── test_patterns.py           # Демонстрація патернів
├── requirements.txt           # Залежності
├── README.md                  # Документація
├── src/
│   ├── core/                 # Ядро системи
│   │   ├── interfaces.py    # Всі інтерфейси (ISP)
│   │   ├── event_system.py  # Observer pattern
│   │   ├── game_state.py    # State pattern
│   │   └── game_engine.py   # Facade pattern
│   ├── entities/             # Істоти
│   │   ├── base.py         # Bridge pattern
│   │   └── factories.py    # Abstract Factory
│   ├── items/               # Предмети
│   │   ├── items.py       # Decorator pattern
│   │   └── inventory.py   # Composite pattern
│   ├── dungeon/            # Підземелля
│   │   ├── room.py       # Composite pattern
│   │   └── builders.py   # Builder pattern
│   ├── combat/            # Бойова система
│   │   └── combat_system.py # Strategy + Template Method
│   └── ui/                # Інтерфейс
│       ├── commands.py   # Command + Chain of Responsibility
│       └── console_ui.py # Adapter pattern
```

## 🔍 Висновок

Проект демонструє практичне застосування 23 патернів проектування в єдиній системі:
- **17 класичних патернів GoF** повністю реалізовані
- **SOLID принципи** дотримані у всій архітектурі
- **GRASP патерни** використані для розподілу відповідальностей

Архітектура дозволяє легко:
- Додавати нові типи монстрів/предметів
- Розширювати стратегії бою
- Змінювати алгоритми генерації підземель
- Додавати нові команди та стани гри

Код структурований, модульний та готовий до масштабування!