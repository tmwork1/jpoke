# Phase 1 設計書: フォルム管理システム

**作成日**: 2026年2月8日  
**Phase**: Phase 1（難易度S）  
**期間**: 2-3月（Week 1-11）  
**目標**: フォルムチェンジ・技固定・複雑特性の実装

---

## 1. Phase 1 概要

### 1.1 実装対象

| カテゴリ | 対象 | 難易度 | 推定工数 |
|---------|------|--------|---------|
| フォルムチェンジ特性 | 5特性 | 🔴 S | 15-20日 |
| 複雑な条件判定特性 | 6特性 | 🔴 S | 10-12日 |
| 技固定系アイテム | 3アイテム | 🔴 S | 7-8日 |
| **合計** | **14要素** | - | **32-40日** |

### 1.2 Phase 1の成果

Phase 1完了で以下が確立される：

1. **フォルム管理システム**: `Pokemon.change_form()`, フォルム別ステータス
2. **技固定ロジック**: `Pokemon.locked_move` 状態管理
3. **動的能力変更**: 特性・タイプの実行時変更
4. **グローバル制御**: かがくへんかガス等の全体影響

→ **これらの基盤があれば、Phase 2以降の実装が加速**

---

## 2. フォルム管理システム設計

### 2.1 技術課題

1. **フォルム別ステータス管理**: 複数フォルムのステータスを保持
2. **動的フォルム変化**: 戦闘中にステータスを即座に変更
3. **フォルム状態の永続化**: 交代後もフォルムを維持
4. **イベント駆動**: フォルム変化をイベントでトリガー

### 2.2 データ構造設計

#### FormData クラス

```python
# src/jpoke/model/pokemon.py

@dataclass
class FormData:
    """フォルム別データ"""
    name: str  # フォルム名（"default", "blade", "shield"等）
    base_stats: Stats  # HP, 攻撃, 防御, 特攻, 特防, 素早さ
    types: tuple[str, str | None]  # タイプ1, タイプ2
    ability: str | None = None  # フォルム固有特性（Noneなら維持）
    weight: float | None = None  # 体重（kg）
```

#### Pokemon クラス拡張

```python
class Pokemon:
    """ポケモンクラス拡張"""
    # 既存属性
    species: str
    level: int
    base_stats: Stats
    types: tuple[str, str | None]
    
    # 新規追加属性
    current_form: str = "default"  # 現在のフォルム
    forms: dict[str, FormData] = field(default_factory=dict)  # フォルム別データ
    form_locked: bool = False  # フォルム固定フラグ（交代でリセットされないフォルム用）
    
    def change_form(self, new_form: str, source: str = "ability") -> bool:
        """
        フォルムを変更する
        
        Args:
            new_form: 変更先フォルム名
            source: 変更トリガー（"ability", "move", "item"）
        
        Returns:
            変更成功したか
        """
        if new_form not in self.forms:
            logger.warning(f"{self.species}に{new_form}フォルムが存在しません")
            return False
        
        if self.current_form == new_form:
            logger.debug(f"既に{new_form}フォルムです")
            return False
        
        old_form = self.current_form
        self.current_form = new_form
        form_data = self.forms[new_form]
        
        # ステータス更新
        self.base_stats = form_data.base_stats
        self.types = form_data.types
        
        # 特性変更（フォルム固有の場合）
        if form_data.ability:
            self._change_ability(form_data.ability)
        
        # イベント発火
        if hasattr(self, 'battle'):
            self.battle.event_manager.fire_event(
                Event.ON_FORM_CHANGE,
                BattleContext(source=self, old_form=old_form, new_form=new_form)
            )
        
        logger.info(f"{self.name}が{old_form}から{new_form}にフォルムチェンジ！")
        return True
    
    def reset_form(self) -> None:
        """フォルムをデフォルトに戻す（交代時等）"""
        if not self.form_locked and self.current_form != "default":
            self.change_form("default")
    
    def _change_ability(self, new_ability: str) -> None:
        """特性を動的に変更"""
        # 既存ハンドラを解除
        if hasattr(self, 'battle'):
            self.unregister_handlers(self.battle.event_manager)
        
        # 新しい特性に変更
        self.ability = AbilityData.get(new_ability)
        
        # 新しいハンドラを登録
        if hasattr(self, 'battle'):
            self.register_handlers(self.battle.event_manager)
```

### 2.3 イベント追加

```python
# src/jpoke/utils/enums/event.py

class Event(Enum):
    # 既存イベント
    ON_SWITCH_IN = "on_switch_in"
    ON_DAMAGE = "on_damage"
    # ... 他
    
    # Phase 1で新規追加
    ON_FORM_CHANGE = "on_form_change"  # フォルム変化時
    ON_BEFORE_FORM_CHANGE = "on_before_form_change"  # フォルム変化前（キャンセル可能）
```

### 2.4 フォルムデータ登録例（ギルガルド）

```python
# src/jpoke/data/pokemon.py

POKEMON_FORMS = {
    "ギルガルド": {
        "default": FormData(
            name="シールドフォルム",
            base_stats=Stats(hp=60, attack=50, defense=150, sp_atk=50, sp_def=150, speed=60),
            types=("はがね", "ゴースト"),
        ),
        "blade": FormData(
            name="ブレードフォルム",
            base_stats=Stats(hp=60, attack=150, defense=50, sp_atk=150, sp_def=50, speed=60),
            types=("はがね", "ゴースト"),
        ),
    },
    "ミミッキュ": {
        "default": FormData(
            name="ばけたすがた",
            base_stats=Stats(hp=55, attack=90, defense=80, sp_atk=50, sp_def=105, speed=96),
            types=("ゴースト", "フェアリー"),
        ),
        "busted": FormData(
            name="ばれたすがた",
            base_stats=Stats(hp=55, attack=90, defense=80, sp_atk=50, sp_def=105, speed=96),
            types=("ゴースト", "フェアリー"),
        ),
    },
}
```

---

## 3. フォルムチェンジ特性実装

### 3.1 ばけのかわ（Week 3-4、最初の実装）

**理由**: 最もシンプル（1回のみのフォルムチェンジ）

```python
# src/jpoke/handlers/ability.py

def ばけのかわ_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """
    ダメージを無効化し、フォルムを変化させる
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（defender=ミミッキュ）
        value: ダメージ量
    
    Returns:
        HandlerReturn(success=True, value=0, control=BLOCK) でダメージ無効
    """
    pokemon = ctx.defender
    
    # 既にばれたすがたなら何もしない
    if pokemon.current_form == "busted":
        return HandlerReturn(False)
    
    # フォルム変化
    pokemon.change_form("busted", source="ability")
    battle.logger.log_message(f"{pokemon.name}のばけのかわがはがれた！")
    
    # ダメージを0にしてブロック
    return HandlerReturn(True, 0, HandlerResult.BLOCK)

# 特性データ登録
ABILITIES["ばけのかわ"] = AbilityData(
    name="ばけのかわ",
    handlers={
        Event.ON_BEFORE_DAMAGE: AbilityHandler(
            ばけのかわ_on_damage,
            subject_spec="defender:self",
            priority=100,  # 最優先で処理
            log="never",  # ログは関数内で出力
        )
    }
)
```

**テスト**:
```python
def test_ばけのかわ():
    """ばけのかわで初回ダメージ無効化"""
    battle = start_battle(
        ally=[Pokemon("ミミッキュ", ability="ばけのかわ")],
        foe=[Pokemon("リザードン")],
    )
    
    # 攻撃前はばけたすがた
    assert battle.ally.active.current_form == "default"
    
    # 攻撃
    execute_move(battle, "たいあたり")
    
    # ダメージ無効、フォルム変化
    assert battle.ally.active.current_hp == battle.ally.active.max_hp
    assert battle.ally.active.current_form == "busted"
    
    # 2回目は普通にダメージ
    execute_move(battle, "たいあたり")
    assert battle.ally.active.current_hp < battle.ally.active.max_hp
```

### 3.2 バトルスイッチ（Week 5-6）

**条件**: 攻撃技使用でブレードフォルム、キングシールド使用でシールドフォルム

```python
def バトルスイッチ_on_try_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """
    技使用前にフォルムを変更
    
    - 攻撃技: ブレードフォルム
    - キングシールド: シールドフォルム
    """
    pokemon = ctx.source
    move = ctx.move
    
    if move.category in ["physical", "special"]:
        # 攻撃技 → ブレードフォルム
        if pokemon.current_form != "blade":
            pokemon.change_form("blade", source="ability")
    elif move.name == "キングシールド":
        # キングシールド → シールドフォルム
        if pokemon.current_form != "default":
            pokemon.change_form("default", source="ability")
    
    return HandlerReturn(True)

ABILITIES["バトルスイッチ"] = AbilityData(
    name="バトルスイッチ",
    handlers={
        Event.ON_TRY_MOVE: AbilityHandler(
            バトルスイッチ_on_try_move,
            subject_spec="source:self",
            priority=10,
            log="never",
        )
    }
)
```

### 3.3 ダルマモード（Week 6-7）

**条件**: HP50%以下でダルマモード発動、HP50%超で通常モードに戻る

```python
def ダルマモード_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """HP50%判定でフォルム変化"""
    pokemon = ctx.defender
    
    hp_percentage = pokemon.current_hp / pokemon.max_hp
    
    if hp_percentage <= 0.5 and pokemon.current_form == "default":
        # ダルマモード発動
        pokemon.change_form("zen", source="ability")
        battle.logger.log_message(f"{pokemon.name}のダルマモードが発動した！")
    elif hp_percentage > 0.5 and pokemon.current_form == "zen":
        # 通常モードに戻る
        pokemon.change_form("default", source="ability")
        battle.logger.log_message(f"{pokemon.name}は通常モードに戻った！")
    
    return HandlerReturn(True)

ABILITIES["ダルマモード"] = AbilityData(
    name="ダルマモード",
    handlers={
        Event.ON_AFTER_DAMAGE: AbilityHandler(
            ダルマモード_on_damage,
            subject_spec="defender:self",
            priority=0,
            log="never",
        )
    }
)
```

---

## 4. 技固定系アイテム（Week 8-9）

### 4.1 技固定ロジック設計

```python
# src/jpoke/model/pokemon.py（Pokemon クラス拡張）

class Pokemon:
    # 新規追加
    locked_move: Move | None = None  # 固定された技
    locked_turns: int = 0  # 固定ターン数（交代でリセット）
    
    def lock_move(self, move: Move) -> None:
        """技を固定する"""
        self.locked_move = move
        self.locked_turns = 0
    
    def unlock_move(self) -> None:
        """技固定を解除する"""
        self.locked_move = None
        self.locked_turns = 0
    
    def is_move_locked(self) -> bool:
        """技が固定されているか"""
        return self.locked_move is not None
```

### 4.2 こだわりハチマキ等の実装

```python
# src/jpoke/handlers/item.py

def こだわり系_on_try_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """
    技選択を制限する
    
    - 最初の技を固定
    - 他の技を選択しようとすると失敗
    """
    pokemon = ctx.source
    move = ctx.move
    
    if not pokemon.is_move_locked():
        # 最初の技を固定
        pokemon.lock_move(move)
        return HandlerReturn(True)
    
    if pokemon.locked_move != move:
        # 異なる技を選択しようとした
        battle.logger.log_message(f"{pokemon.name}は{pokemon.locked_move.name}しか使えない！")
        return HandlerReturn(False, control=HandlerResult.BLOCK)
    
    return HandlerReturn(True)

def こだわり系_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """交代時に技固定を解除"""
    pokemon = ctx.source
    pokemon.unlock_move()
    return HandlerReturn(True)

# こだわりハチマキ
ITEMS["こだわりハチマキ"] = ItemData(
    name="こだわりハチマキ",
    handlers={
        Event.ON_TRY_MOVE: ItemHandler(
            こだわり系_on_try_move,
            subject_spec="source:self",
            priority=10,
            log="never",
        ),
        Event.ON_SWITCH_OUT: ItemHandler(
            こだわり系_on_switch_out,
            subject_spec="source:self",
            priority=0,
            log="never",
        ),
        Event.ON_CALC_ATTACK: ItemHandler(
            lambda b, ctx, v: HandlerReturn(True, (v * 6144) // 4096),  # 1.5倍
            subject_spec="source:self",
            log="never",
        ),
    }
)
```

---

## 5. 複雑特性（Week 10-11）

### 5.1 かがくへんかガス

**効果**: 場にいる間、他のポケモンの特性が発動しなくなる

```python
# src/jpoke/core/battle.py（Battle クラス拡張）

class Battle:
    # 新規追加
    ability_suppression: bool = False  # 特性抑制フラグ
    suppression_source: Pokemon | None = None  # 抑制元
```

```python
# src/jpoke/handlers/ability.py

def かがくへんかガス_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """特性抑制を開始"""
    battle.ability_suppression = True
    battle.suppression_source = ctx.source
    battle.logger.log_message(f"{ctx.source.name}のかがくへんかガスが発動！")
    return HandlerReturn(True)

def かがくへんかガス_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """特性抑制を解除"""
    battle.ability_suppression = False
    battle.suppression_source = None
    battle.logger.log_message(f"かがくへんかガスの効果が消えた！")
    return HandlerReturn(True)

ABILITIES["かがくへんかガス"] = AbilityData(
    name="かがくへんかガス",
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(
            かがくへんかガス_on_switch_in,
            subject_spec="source:self",
            priority=200,  # 最優先
            log="never",
        ),
        Event.ON_SWITCH_OUT: AbilityHandler(
            かがくへんかガス_on_switch_out,
            subject_spec="source:self",
            priority=0,
            log="never",
        ),
    }
)
```

**EventManager への影響**:

```python
# src/jpoke/core/event.py（EventManager 拡張）

def fire_event(self, event: Event, ctx: BattleContext) -> List[HandlerReturn]:
    """イベント発火"""
    # 特性抑制中は特性ハンドラをスキップ
    handlers = self.get_handlers(event)
    
    if self.battle.ability_suppression:
        handlers = [
            h for h in handlers
            if not isinstance(h, AbilityHandler) or h.owner == self.battle.suppression_source
        ]
    
    # ハンドラ実行
    return self._execute_handlers(handlers, ctx)
```

---

## 6. テスト戦略

### 6.1 フォルムチェンジテスト

```python
def test_form_change_basic():
    """基本的なフォルム変化"""
    battle = start_battle(ally=[Pokemon("ギルガルド", ability="バトルスイッチ")])
    
    # 初期はシールドフォルム
    assert battle.ally.active.current_form == "default"
    assert battle.ally.active.base_stats.defense == 150
    
    # 攻撃技使用でブレードフォルム
    execute_move(battle, "シャドーボール")
    assert battle.ally.active.current_form == "blade"
    assert battle.ally.active.base_stats.attack == 150
```

### 6.2 技固定テスト

```python
def test_こだわりハチマキ_技固定():
    """こだわりハチマキで技固定"""
    battle = start_battle(
        ally=[Pokemon("ガブリアス", item="こだわりハチマキ", moves=["じしん", "げきりん"])]
    )
    
    # 最初はじしん使用
    execute_move(battle, "じしん")
    
    # 次はげきりんを選択しようとする
    result = try_select_move(battle, "げきりん")
    assert not result.success  # 選択失敗
    
    # じしんは選択できる
    result = try_select_move(battle, "じしん")
    assert result.success
```

---

## 7. Phase 1 完了条件

- ✅ フォルム管理システム完成
- ✅ 5種のフォルムチェンジ特性実装（ばけのかわ、バトルスイッチ、ダルマモード、アイスフェイス、ぎょぐん）
- ✅ こだわり系3アイテム実装（ハチマキ、メガネ、スカーフ）
- ✅ 複雑特性6種実装（かがくへんかガス、こだいかっせい等）
- ✅ 統合テスト全パス
- ✅ 設計文書完成

---

**Status**: Phase 1 設計完了  
**Next**: Week 1-2 でフォルム管理システム実装開始
