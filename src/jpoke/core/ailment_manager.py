"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model.pokemon import Pokemon
from jpoke.model.ailment import Ailment
from jpoke.types import AilmentName
from jpoke.enums import Event, LogCode
from .context import EventContext
from .log_payload import AilmentPayload
from jpoke.utils import fast_copy


class AilmentManager:
    """ポケモンの状態異常を管理するクラス。

    状態異常の付与、治療、ターン経過処理を担当。
    Pokemonクラスから状態異常管理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        self.battle = battle

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def _events(self) -> EventManager:
        return self.battle.events

    def apply(self,
              target: Pokemon,
              name: AilmentName,
              count: int | None = None,
              source: Pokemon | None = None,
              overwrite: bool = False,
              allow_type_immunity_bypass: bool = True) -> bool:
        """状態異常を付与する。

        Args:
            target: 対象のポケモン
            name: 状態異常名
            count: 継続ターン数（ねむりは省略時に Champions 仕様で自動決定）
            source: 状態異常の原因となったポケモン
            overwrite: Trueの場合、既存の状態異常を上書き
            allow_type_immunity_bypass: Falseの場合、source の特性（ふしょく等）による
                どく/はがねタイプへのどく・もうどく無効貫通を無効化する。どくびしのように
                「付与元は存在するが特性によるタイプ無効貫通の対象ではない」経路で使う
                （どくびしはふしょく持ちが自分自身に踏んでも、はがねタイプ等ならどく状態にはならない）。
        Returns:
            付与に成功したTrue

        Note:
            - overwrite=Falseの場合、既に状態異常があれば失敗
            - 同じ状態異常の重ね掛けは不可
            - ねむりの count=None 時は Champions 仕様で自動決定（2: 1/3、3: 2/3）
            - targetが瀕死（HP0）の場合は付与しない。技の追加効果等でダメージにより
              瀕死になった相手には状態異常が付与されないため（実機仕様）
        """
        # 瀕死のポケモンには状態異常を付与しない
        if target.fainted:
            return False

        # ねむりのcountをChampions仕様で自動決定（count=Noneのとき）
        if name == "ねむり" and count is None:
            count = 2 if self.battle.random.random() < 1 / 3 else 3

        # overwrite=True でない限り上書き不可
        if target.ailment.is_active and not overwrite:
            return False

        # overwrite=True でも uncurable は上書き不可
        if target.ailment.is_active and target.ailment.uncurable:
            return False

        # 重ねがけ不可
        if name == target.ailment.name:
            return False

        # タイプによる無効化をチェック
        type_immunity_source = source if allow_type_immunity_bypass else None
        if not self._can_apply_by_type(name, target, type_immunity_source):
            self.battle.add_event_log(
                target,
                LogCode.AILMENT_PREVENTED,
                payload=AilmentPayload(
                    ailment=name,
                    source=source.name if source else None,
                    display_reason="タイプ無効",
                )
            )
            return False

        # ON_BEFORE_APPLY_AILMENT イベントを発火して特性などによる無効化をチェック
        apply_ctx = EventContext(source=source, target=target)

        # ハンドラーが空値を返した場合は状態異常を付与しない
        resolved_name = self._events.emit(Event.ON_BEFORE_APPLY_AILMENT, apply_ctx, name)
        if not resolved_name:
            return False

        # overwriteで既存の状態異常を上書きする場合は解除ログを出力
        if target.ailment.is_active:
            self.battle.add_event_log(
                target,
                LogCode.AILMENT_REMOVED,
                payload=AilmentPayload(ailment=target.ailment.name)
            )

        # 既存のハンドラを削除
        target.ailment.unregister_handlers(self._events, target)

        # 新しい状態異常を設定してハンドラ登録
        self.battle.add_event_log(
            target,
            LogCode.AILMENT_APPLIED,
            payload=AilmentPayload(ailment=resolved_name, source=source.name if source else None)
        )
        target.ailment = Ailment(resolved_name, count=count)
        target.ailment.register_handlers(self._events, target)

        # 付与後イベントを発火（シンクロ等のリアクション用）
        self._events.emit(Event.ON_APPLY_AILMENT, apply_ctx, resolved_name)
        return True

    def _can_apply_by_type(self,
                           ailment: AilmentName,
                           target: Pokemon,
                           source: Pokemon | None) -> bool:
        """タイプによって状態異常を付与できるか判定する。"""
        match ailment:
            case "どく" | "もうどく":
                if source is not None and source.ability.name == "ふしょく":
                    return True
                return not (target.has_type("どく") or target.has_type("はがね"))
            case "やけど":
                return not target.has_type("ほのお")

            case "まひ":
                return not target.has_type("でんき")

            case "こおり":
                return not target.has_type("こおり")

        return True

    def remove(self, target: Pokemon) -> bool:
        """状態異常を解除する。

        Args:
            target: 対象のポケモン

        Returns:
            解除に成功したらTrue
        """
        if not target.ailment.is_active:
            return False

        # 回復不能な状態異常は解除しない
        if target.ailment.uncurable:
            return False

        self.battle.add_event_log(
            target,
            LogCode.AILMENT_REMOVED,
            payload=AilmentPayload(ailment=target.ailment.name)
        )
        target.ailment.unregister_handlers(self._events, target)
        target.ailment = Ailment()
        return True

    def tick(self, target: Pokemon) -> bool:
        """状態異常のターン経過処理を行う。

        Args:
            target: 対象のポケモン

        Returns:
            ターン経過処理を行った場合True、状態異常がない場合False
        """
        if not target.ailment.is_active:
            return False
        target.ailment.tick()
        if target.ailment.count == 0:
            self.remove(target)
        return True
