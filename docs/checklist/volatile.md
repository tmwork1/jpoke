# Volatile ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## チェックリスト

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| こんらん | 33%確率で自傷ダメージ、自然治癒 | ON_BEFORE_ACTION | こんらん_action | ✅ | ✅ | ❌ | test_volatile.py |
| ちょうはつ | 変化技の使用禁止 | ON_BEFORE_MOVE | ちょうはつ_before_move | ✅ | ✅ | ❌ | test_volatile.py |
| ちょうはつ | ターン経過でカウント減少・解除 | ON_TURN_END | ちょうはつ_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| バインド | ターン終了時1/8ダメージ、カウント減少 | ON_TURN_END | バインド_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| バインド | 交代制限 | ON_CHECK_TRAPPED | バインド_before_switch | ✅ | ✅ | ❌ | test_volatile.py |
| メロメロ | 行動不能（50%） | ON_BEFORE_ACTION | メロメロ_action | ✅ | ✅ | ❌ | test_volatile.py |
| かなしばり | 特定技の使用禁止 | ON_BEFORE_MOVE | かなしばり_before_move | ✅ | ✅ | ❌ | test_volatile.py |
| かなしばり | ターン経過でカウント減少・解除 | ON_TURN_END | かなしばり_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| バインド | 使用者の交代時にバインド解除 | ON_SWITCH_OUT | バインド_source_switch_out | ✅ | ❌ | ❌ |  |
| あめまみれ | ターン経過でカウント減少・解除 | ON_TURN_END | あめまみれ_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| かいふくふうじ | ターン経過でカウント減少・解除 | ON_TURN_END | かいふくふうじ_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| じごくずき | ターン経過でカウント減少・解除 | ON_TURN_END | じごくずき_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| じゅうでん | ターン経過でカウント減少・解除 | ON_TURN_END | じゅうでん_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| でんじふゆう | ターン経過でカウント減少・解除 | ON_TURN_END | でんじふゆう_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| にげられない | 交代制限 | ON_CHECK_TRAPPED | にげられない_check_trapped | ✅ | ✅ | ❌ | test_volatile.py |
| ねむけ | ターン経過でカウント減少、ねむり移行 | ON_TURN_END | ねむけ_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| ねをはる | 交代制限 | ON_CHECK_TRAPPED | ねをはる_check_trapped | ✅ | ✅ | ❌ | test_volatile.py |
| ほろびのうた | ターン経過で気絶 | ON_TURN_END | ほろびのうた_turn_end | ✅ | ✅ | ❌ | test_volatile.py |
| ひるみ | 行動不能、ターン終了で解除 | ON_TRY_ACTION/ON_TURN_END | ひるみ_action/ひるみ_turn_end | ✅ | ✅ | ❌ | test_move.py |
