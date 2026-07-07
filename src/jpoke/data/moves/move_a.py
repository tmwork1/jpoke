"""技データ定義モジュール（あ行のエントリ）。

`data/move.py` から分割された、MOVES辞書の一部を定義する。
分割・並び替えは scripts/sort_data/sort_moves.py が行うため、手編集時も
五十音順を維持すること。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core import LethalHandler
from jpoke.types import MoveName

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs
from jpoke.handlers import lethal as l

from ..models import MoveData


MOVES_A: dict[MoveName, MoveData] = {
    "アイアンテール": MoveData(
        type="はがね",
        category="physical",
        pp=16,
        power=100,
        accuracy=75,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンテール_lower_defender_def,
            )
        }
    ),
    "アイアンヘッド": MoveData(
        type="はがね",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンヘッド_apply_flinch,
            )
        }
    ),
    "アイアンローラー": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=130,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.アイアンローラー_check_terrain,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンローラー_clear_terrain,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "アイススピナー": MoveData(
        type="こおり",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイススピナー_clear_terrain,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "アイスハンマー": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=100,
        accuracy=90,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アイスハンマー_lower_attacker_spe,
            )
        }
    ),
    "あおいほのお": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=130,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あおいほのお_apply_burn_to_defender,
            )
        }
    ),
    "アクアカッター": MoveData(
        type="みず",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "アクアジェット": MoveData(
        type="みず",
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアステップ": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact", "dance", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アクアステップ_boost_attacker_spe,
            )
        }
    ),
    "アクアテール": MoveData(
        type="みず",
        category="physical",
        pp=12,
        power=90,
        accuracy=90,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアブレイク": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=85,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アクアブレイク_lower_defender_def,
            )
        }
    ),
    "アクアリング": MoveData(
        type="みず",
        category="status",
        pp=20,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アクアリング_apply,
            ),
        }
    ),
    "あくうせつだん": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=100,
        accuracy=95,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "アクセルブレイク": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.効果抜群時威力ブースト,
            )
        },
    ),
    "アクセルロック": MoveData(
        type="いわ",
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あくのはどう": MoveData(
        type="あく",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あくのはどう_apply_flinch,
            )
        }
    ),
    "あくび": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.あくび_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あくび_apply,
            ),
        }
    ),
    "あくまのキッス": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        accuracy=75,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あくまのキッス_apply_ailment_to_defender,
            ),
        }
    ),
    "アクロバット": MoveData(
        type="ひこう",
        category="physical",
        pp=16,
        power=55,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.アクロバット_double_power_when_no_item,
            ),
        },
    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "アシストパワー": MoveData(
        type="エスパー",
        category="special",
        pp=12,
        power=20,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.アシストパワー_boost_power_by_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "アシッドボム": MoveData(
        type="どく",
        category="special",
        pp=20,
        power=40,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アシッドボム_sharply_lower_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.アシッドボム_reduce_spd)
        }
    ),
    "アストラルビット": MoveData(
        type="ゴースト",
        category="special",
        pp=8,
        power=120,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "あてみなげ": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=70,
        accuracy=None,
        priority=-1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あなをほる": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "あなをほる"),
            ),
        }
    ),
    "あばれる": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "アフロブレイク": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アフロブレイク_recoil,
            )
        }
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまいかおり_modify_defender_stats,
            )
        }
    ),
    "あまえる": MoveData(
        type="フェアリー",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまえる_modify_defender_stats,
            )
        }
    ),
    "あまごい": MoveData(
        type="みず",
        category="status",
        pp=5,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまごい_activate_weather,
            ),
        }
    ),
    "あやしいかぜ": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=60,
        accuracy=100,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あやしいかぜ_boost_all_stats,
            )
        }
    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あやしいひかり_apply,
            ),
        }
    ),
    "アロマセラピー": MoveData(
        type="くさ",
        category="status",
        pp=5,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アロマセラピー_apply,
            ),
        },
    ),
    "アロマミスト": MoveData(
        type="フェアリー",
        category="status",
        pp=20,
        target="self",
        handlers={},  # 追加効果なし
    ),
    "あわ": MoveData(
        type="みず",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あわ_lower_defender_spd,
            )
        }
    ),
    "あんこくきょうだ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=75,
        accuracy=100,
        critical_rank=3,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        accuracy=100,
        flags={"non_encore"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.アンコール_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アンコール_apply,
            )
        }
    ),
    "アーマーキャノン": MoveData(
        type="ほのお",
        category="special",
        pp=8,
        power=120,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アーマーキャノン_lower_attacker_stats,
            )
        }
    ),
    "アームハンマー": MoveData(
        type="かくとう",
        category="physical",
        pp=12,
        power=100,
        accuracy=90,
        flags={"contact", "punch"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アームハンマー_lower_attacker_spe,
            )
        }
    ),
    "いえき": MoveData(
        type="どく",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.いえき_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いえき_apply,
            ),
        }
    ),
    "イカサマ": MoveData(
        type="あく",
        category="physical",
        pp=16,
        power=95,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "いかりのこな": MoveData(
        type="むし",
        category="status",
        pp=20,
        priority=2,
        handlers={},  # 追加効果なし
    ),
    "いかりのまえば": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        accuracy=90,
        flags={"contact", "fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.half_damage,
                subject_spec="attacker:self",
                priority=15,
            )
        }
    ),
    "いじげんホール": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=80,
        accuracy=None,
        flags={"unprotectable", "bypass_substitute"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.いじげんホール_remove_protect,
            )
        }
    ),
    "いじげんラッシュ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=100,
        accuracy=None,
        flags={"unprotectable", "bypass_substitute"},
        handlers={
            Event.ON_HIT: [
                h.MoveHandler(ha.いじげんラッシュ_remove_protect),
                h.MoveHandler(ha.いじげんラッシュ_lower_attacker_def),
            ]
        }
    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いたみわけ_equalize_hp,
            )
        }
    ),
    "いちゃもん": MoveData(
        type="あく",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いちゃもん_apply,
            ),
        }
    ),
    "いっちょうあがり": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},  # 追加効果自体は無いが、ちからずく対象技として扱われる（docs/spec/abilities/ちからずく.md参照）
        handlers={},  # しれいとう連携のランクアップはダブル専用のため対象外（実装しない）
    ),
    "いてつくしせん": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いてつくしせん_apply_freeze_to_defender,
            ),
        }
    ),
    "いとをはく": MoveData(
        type="むし",
        category="status",
        pp=40,
        accuracy=95,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いとをはく_reduce_defender_spe,
            ),
        }
    ),
    "イナズマドライブ": MoveData(
        type="でんき",
        category="special",
        pp=8,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.効果抜群時威力ブースト,
            )
        },
    ),
    "いにしえのうた": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いにしえのうた_apply_sleep_to_defender,
            )
        }
    ),
    "いのちがけ": MoveData(
        type="かくとう",
        category="special",
        pp=5,
        power=0,
        accuracy=100,
        flags={"fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.いのちがけ_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "いのちのしずく": MoveData(
        type="みず",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いのちのしずく_heal,
            ),
        }
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いばる_apply,
            ),
        }
    ),
    "いびき": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=50,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.いびき_check_sleep,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いびき_apply_flinch,
            )
        }
    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのすず_cure_ailment,
            ),
        }
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのねがい_apply,
            ),
        }
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのはどう_heal_defender,
            ),
        }
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        accuracy=85,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやなおと_lower_defender_def,
            )
        }
    ),
    "いわおとし": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=50,
        accuracy=90,
        handlers={},  # 追加効果なし
    ),
    "いわくだき": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわくだき_lower_defender_def,
            )
        }
    ),
    "いわなだれ": MoveData(
        type="いわ",
        category="physical",
        pp=10,
        power=75,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわなだれ_apply_flinch,
            )
        }
    ),
    "インファイト": MoveData(
        type="かくとう",
        category="physical",
        pp=8,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.インファイト_lower_attacker_stats,
            )
        }
    ),
    "ウェザーボール": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=50,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.ウェザーボール_modify_move_type,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ウェザーボール_power_modifier,
            ),
        },
    ),
    "ウェーブタックル": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウェーブタックル_recoil,
            )
        }
    ),
    "うずしお": MoveData(
        type="みず",
        category="special",
        pp=15,
        power=35,
        accuracy=85,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "うそなき": MoveData(
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うそなき_reduce_defender_spe,
            )
        }
    ),
    "うたう": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        accuracy=55,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うたう_apply_sleep,
            ),
        }
    ),
    "うたかたのアリア": MoveData(
        type="みず",
        category="special",
        pp=12,
        power=90,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うたかたのアリア_cure_defender_burn,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.うたかたのアリア_cure_defender_burn)
        }
    ),
    "うちおとす": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=50,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.うちおとす_apply_grounded,
            )
        },
    ),
    "ウッドハンマー": MoveData(
        type="くさ",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウッドハンマー_recoil,
            )
        }
    ),
    "ウッドホーン": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=75,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ウッドホーン_drain, priority=20)
        }
    ),
    "うっぷんばらし": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.うっぷんばらし_double_power_when_rank_dropped,
            ),
        }
    ),
    "うつしえ": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "うらみ": MoveData(
        type="ゴースト",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.うらみ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うらみ_deplete_pp,
            ),
        }
    ),
    "うらみつらみ": MoveData(
        type="ゴースト",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うらみつらみ_lower_defender_atk,
            )
        }
    ),
    "エアカッター": MoveData(
        type="ひこう",
        category="special",
        pp=25,
        power=60,
        accuracy=95,
        critical_rank=1,
        flags={"slash", "wind"},
        handlers={},  # 追加効果なし
    ),
    "エアスラッシュ": MoveData(
        type="ひこう",
        category="special",
        pp=15,
        power=75,
        accuracy=95,
        flags={"slash", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エアスラッシュ_apply_flinch,
            )
        }
    ),
    "エアロブラスト": MoveData(
        type="ひこう",
        category="special",
        pp=5,
        power=100,
        accuracy=95,
        critical_rank=1,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "エコーボイス": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=40,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "えだづき": MoveData(
        type="くさ",
        category="physical",
        pp=40,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "エナジーボール": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エナジーボール_lower_defender_spd,
            )
        }
    ),
    "エレキネット": MoveData(
        type="でんき",
        category="special",
        pp=15,
        power=55,
        accuracy=95,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エレキネット_lower_defender_spd,
            )
        }
    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.エレキフィールド_activate_terrain,
            ),
        }
    ),
    "エレキボール": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=1,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.エレキボール_calc_power,
            ),
        }
    ),
    "エレクトロビーム": MoveData(
        type="でんき",
        category="special",
        pp=12,
        power=130,
        accuracy=100,
        handlers={
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.エレクトロビーム_boost_spa,
                    priority=50,
                ),
                h.MoveHandler(
                    ha.エレクトロビーム_weather_skip,
                    priority=90,
                ),
                h.MoveHandler(
                    ha.エレクトロビーム_charge,
                ),
            ],
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_MOVE: LethalHandler(l.エレクトロビーム_boost_spa)
        }
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.えんまく_modify_defender_stats,
            )
        }
    ),
    "おいかぜ": MoveData(
        type="ひこう",
        category="status",
        pp=15,
        target="own_side",
        flags={"wind"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おいかぜ_set_side_field,
            ),
        }
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        flags={"non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.おかたづけ_cleanup),
        }
    ),
    "おきみやげ": MoveData(
        type="あく",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おきみやげ_apply,
            ),
        }
    ),
    "オクタンほう": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=110,
        accuracy=85,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.オクタンほう_lower_acc,
            )
        }
    ),
    "おさきにどうぞ": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        handlers={},  # 追加効果なし
    ),
    "おしゃべり": MoveData(
        type="ひこう",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おしゃべり_apply_confusion,
            )
        }
    ),
    "おたけび": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おたけび_modify_defender_stats,
            ),
        }
    ),
    "おだてる": MoveData(
        type="あく",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おだてる_apply,
            ),
        }
    ),
    "おちゃかい": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        handlers={},  # 追加効果なし
    ),
    "おどろかす": MoveData(
        type="ゴースト",
        category="physical",
        pp=15,
        power=30,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おどろかす_apply_flinch,
            )
        }
    ),
    "おにび": MoveData(
        type="ほのお",
        category="status",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おにび_apply_burn,
            ),
        }
    ),
    "おはかまいり": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.おはかまいり_calc_power,
            ),
        }
    ),
    "オーバードライブ": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "オーバーヒート": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーバーヒート_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.オーバーヒート_lower_attacker_spa)
        }
    ),
    "オーラウイング": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        critical_rank=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーラウイング_boost_attacker_spe,
            )
        }
    ),
    "オーラぐるま": MoveData(
        type="でんき",
        category="physical",
        pp=10,
        power=110,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.オーラぐるま_check_move_type,
            ),
        },
    ),
    "オーロラビーム": MoveData(
        type="こおり",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.オーロラビーム_lower_defender_atk,
            )
        }
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="status",
        pp=20,
        target="own_side",
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.オーロラベール_check_weather,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.オーロラベール_apply,
            ),
        }
    ),
}
