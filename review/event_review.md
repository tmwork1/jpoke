総評（先に結論）

👍 ポケモンバトル向けイベントシステムとして非常に良い

👍 priority / once / source 制御は実戦向け

👍 deepcopy + update_reference の発想は高度

⚠️ ただし

Handler の key 設計

emit の責務肥大

triggered_by 判定

Context の曖昧さ
は将来の拡張で効いてくる

👉 「バトル専用 EventBus」としては正解
👉 「汎用 EventSystem」に進化させるなら分離が必要

① EventContext の設計レビュー
@dataclass
class EventContext:
    source: Pokemon
    by: Side = "self"
    move: Move = None
    field: GlobalField | SideField | Weather | Terrain = ""

良い点

source を必須にしている → 正しい

バトル文脈に特化している → jpoke 向き

問題点
❌ 型が「なんでも入る箱」になりつつある

field が 4種 union

move が Optional だが型的に不明確

by が source から派生できそう

改善案（将来向け）
案1：Context は「最小限」
@dataclass
class EventContext:
    source: Pokemon
    target: Pokemon | None = None
    move: Move | None = None


副作用（field / weather / terrain）は Battle から引く

案2：Context 派生クラス（上級）
class DamageContext(EventContext): ...
class SwitchContext(EventContext): ...


👉 IDE補完・F12 が強くなる

② Handler を dict の key にしている点
self.handlers: dict[Event, dict[Handler, list[Pokemon | Player]]]

良い点

Handler を immutable（frozen=True）

priority / once を含めた一意性

⚠️ 将来バグポイント

func が key → 同じ関数でも別 Handler

deepcopy 時の同一性が直感的でない

off がやや危険（同じ func でも handler が違うと消えない）

改善案（強く推奨）
@dataclass(frozen=True)
class Handler:
    id: str
    func: Callable
    priority: int = 0
    triggered_by: Side = "self"
    once: bool = False


または

handlers: dict[Event, list[HandlerEntry]]

@dataclass
class HandlerEntry:
    handler: Handler
    sources: list[Pokemon | Player]


👉 構造を1段平坦にすると安全

③ triggered_by 判定ロジック（重要）
if (handler.triggered_by == "self" and ctx.source in sources) or \
   (handler.triggered_by == "foe" and any(ctx.source is not mon for mon in sources)):

問題点

foe 判定が 論理的に弱い

any(ctx.source is not mon) はほぼ常に True

正しい意味は？

おそらく：

「source が登録者と敵対しているか」

改善案（Battle に委譲）
if handler.triggered_by == "self":
    cond = ctx.source in sources
elif handler.triggered_by == "foe":
    cond = any(self.battle.is_foe(ctx.source, s) for s in sources)


👉 敵味方判定は EventManager がやるべきでない

④ emit が責務過多
def emit(self, event, ctx, value):


この中でやっていること：

handler 取得

source → ctx 生成

素早さ順並び替え

handler 実行

once 管理

STOP 制御

value 変換

問題

テストしにくい

将来デバッグ地獄

改善案（分割）
def emit(...):
    ctxs = self._resolve_contexts(...)
    for handler in self._iter_handlers(event):
        value = self._call_handler(handler, ctxs, value)
    return value


👉 ロジックが読めるようになる

⑤ HandlerResult の扱いはとても良い
class HandlerResult(Enum):
    STOP_HANDLER
    STOP_EVENT


👍 Showdown 互換思想として非常に良い

ただし：

elif isinstance(res, tuple):
    value, flag = res

改善案（明示型）
@dataclass
class HandlerResponse:
    value: Any
    result: HandlerResult | None


IDE補完が爆上がりします。

⑥ deepcopy + update_reference は高度だが危険
良い点

シミュレーション・分岐探索向き

AI 探索との相性が最高

問題点

source 特定が インデックス依存

将来 Player / Pokemon の構造変更で壊れる

改善案（将来）

Pokemon / Player に 永続 ID を持たせる

index ではなく ID で再紐付け

最終まとめ（設計判断）
観点	評価
バトル特化	◎
拡張性	◯
IDEフレンドリー	△
AI探索向け	◎
将来保守	△
今すぐ直すべき

triggered_by の foe 判定

emit の責務整理

後回しでよい

Handler key 設計

Context 分割