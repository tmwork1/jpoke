from jpoke.model import Move
from jpoke.core.context import BattleContext
import test_utils as t
from jpoke.core.event import Event
from jpoke import Pokemon
import sys
sys.path.insert(0, 'tests')


# テスト: ノーガード（防御側）の場合に必中化される
battle = t.start_battle(
    ally=[Pokemon('テッポウオ', moves=['かみなり'])],
    foe=[Pokemon('ピカチュウ', ability='ノーガード')]  # 防御側がノーガード
)

print("=== 防御側がノーガード持ちの場合 ===")
attacker = battle.actives[0]
defender = battle.actives[1]
print(f"攻撃側: {attacker.name} (ability: {attacker.ability.name})")
print(f"防御側: {defender.name} (ability: {defender.ability.name})")

# ON_MODIFY_ACCURACY イベントを発火

# フレイムオブレアは40%命中なので、ここで適用される
initial_accuracy = 40

# コンテキストを作成（簡略化）


class SimpleCtx:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender


ctx = SimpleCtx(attacker, defender)

# イベント発火
accuracy_result = battle.events.emit(Event.ON_MODIFY_ACCURACY, ctx, initial_accuracy)
print(f"\n命中率 '{initial_accuracy}' -> '{accuracy_result}'")
print(f"期待値: None (必中)")
print(f"実際: {accuracy_result}")
print(f"ノーガード必中化成功: {accuracy_result is None}")
