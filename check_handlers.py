import test_utils as t
from jpoke.core.event import Event
from jpoke import Pokemon
import sys
sys.path.insert(0, 'tests')


# ノーガード持ちのポケモンを作成してバトルを開始
battle = t.start_battle(
    ally=[Pokemon('テッポウオ', ability='ノーガード')],
    foe=[Pokemon('ピカチュウ')]
)

# ノーガードのハンドラが幾つ登録されているか確認
no_guard_ability = battle.actives[0].ability
handlers_dict = no_guard_ability.data.handlers
print(f'handlers dict keys: {handlers_dict.keys()}')
print(f'ON_MODIFY_ACCURACY: {handlers_dict.get(Event.ON_MODIFY_ACCURACY)}')
print(f'type: {type(handlers_dict.get(Event.ON_MODIFY_ACCURACY))}')
if isinstance(handlers_dict.get(Event.ON_MODIFY_ACCURACY), list):
    handlers_list = handlers_dict.get(Event.ON_MODIFY_ACCURACY)
    print(f'number of handlers: {len(handlers_list)}')
    for i, h in enumerate(handlers_list):
        print(f'  handler {i}: {h}')
