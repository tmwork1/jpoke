# 検討記録: core/*_manager.py 等をクラスではなく関数モジュールにすべきか

更新日: 2026-07-04

## 対象TODO（検討済み・解消）

以下8ファイル冒頭にあった同一趣旨のTODOコメントに対する検討結果。

- `src/jpoke/core/ability_manager.py`
- `src/jpoke/core/ailment_manager.py`
- `src/jpoke/core/command_manager.py`
- `src/jpoke/core/item_manager.py`
- `src/jpoke/core/query.py`
- `src/jpoke/core/speed_calculator.py`
- `src/jpoke/core/status_manager.py`（TODOコメントは2箇所）
- `src/jpoke/core/volatile_manager.py`

## 結論

**現状のクラス設計を維持する。** TODOコメントは削除済み。

## 理由

いずれのクラスも以下の共通構造を持つ：

```python
def __init__(self, battle: Battle):
    self.battle = battle

def __deepcopy__(self, memo):
    cls = self.__class__
    new = cls.__new__(cls)
    memo[id(self)] = new
    fast_copy(self, new, keys_to_deepcopy=[])
    return new

def update_reference(self, battle: Battle):
    self.battle = battle
```

`Battle` はシミュレーション・先読み用途で頻繁にディープコピーされる。各マネージャーは
`Battle` への逆参照を持つため、素直に `deepcopy` すると循環参照を再帰的にたどってしまう。
上記の `__deepcopy__`/`update_reference` は、その循環を断ち切りつつ `Battle` 側から
コピー後に参照を張り替えるための仕組みであり、クラス設計そのものに起因する複雑さではなく
「`Battle` を安全にディープコピーする」という要件から生まれている。

関数モジュール化した場合、この `__deepcopy__`/`update_reference` の定型コード（1ファイルあたり
約10行×8ファイル）は削除できる一方、各マネージャーの呼び出し箇所（`ability_manager` 関連6箇所、
`item_manager` 関連29箇所、`ailment_manager` 関連47箇所、`volatile_manager` 関連69箇所、
`status_manager` 関連3箇所、`command_manager` 関連10箇所、`query` 関連79箇所、
`speed_calculator` 関連8箇所、計約250箇所）を「`self.xxx_manager.method(...)` → `xxx_manager.method(battle, ...)`」
という形に書き換える必要がある。関数シグネチャに `battle` を都度明示的に渡すだけで、
実質的な設計や責務分担は変わらないため、シンプルさの向上に対してリスク（大量の機械的書き換えによる
デグレ混入）が見合わない。

## 今後について

「Battleの状態そのものを見直す」等の大きな理由が別途生まれない限り、この設計を維持する。
もし将来的に関数モジュール化を進める場合は、1マネージャーずつ個別のリファクタタスクとして
（呼び出し箇所の書き換えとテスト実行をセットで）計画すること。一括での書き換えは避ける。
