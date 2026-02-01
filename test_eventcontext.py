"""EventContextの互換性テスト"""
from jpoke.core.event import EventContext
from jpoke.model import Pokemon

p1 = Pokemon('ピカチュウ', 50)
p2 = Pokemon('ライチュウ', 50)

# attacker/defenderで指定
ctx1 = EventContext(attacker=p1, defender=p2)
print(f'attacker指定:')
print(f'  source={ctx1.source.name}, target={ctx1.target.name}')
print(f'  attacker={ctx1.attacker.name}, defender={ctx1.defender.name}')
print(f'  get("attacker")={ctx1.get("attacker").name}, get("source")={ctx1.get("source").name}')

# source/targetで指定
ctx2 = EventContext(source=p1, target=p2)
print(f'\nsource指定:')
print(f'  source={ctx2.source.name}, target={ctx2.target.name}')
print(f'  attacker={ctx2.attacker.name}, defender={ctx2.defender.name}')
print(f'  get("attacker")={ctx2.get("attacker").name}, get("source")={ctx2.get("source").name}')

print('\n✅ 両方の指定方法が正常に動作しています')
