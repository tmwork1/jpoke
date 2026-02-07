# Ability ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## すべて

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| ありじごく | 宙に浮いていないポケモンを捕捉 | ON_CHECK_TRAPPED | ありじごく | ✅ | ✅ | ❌ | test_ability.py |
| かげふみ | かげふみ以外を捕捉 | ON_CHECK_TRAPPED | かげふみ | ✅ | ✅ | ❌ | test_ability.py |
| じりょく | はがねタイプを捕捉 | ON_CHECK_TRAPPED | じりょく | ✅ | ✅ | ❌ | test_ability.py |
| かちき | 能力ダウン時に特攻+2 | ON_MODIFY_STAT | かちき | ✅ | ✅ | ❌ | test_ability.py |
| すなかき | 砂嵐時に素早さ2倍 | ON_CALC_SPEED | すなかき | ✅ | ❌ | ❌ |  |
| めんえき | どく・もうどく状態を防ぐ | ON_BEFORE_APPLY_AILMENT | めんえき | ✅ | ✅ | ❌ | test_ability.py |
| ふみん | ねむり状態を防ぐ | ON_BEFORE_APPLY_AILMENT | ふみん | ✅ | ✅ | ❌ | test_ability.py |
| やるき | ねむり状態を防ぐ | ON_BEFORE_APPLY_AILMENT | やるき | ✅ | ✅ | ❌ | test_ability.py |
| マイペース | こんらん状態を防ぐ（揮発状態） | ON_BEFORE_APPLY_AILMENT | マイペース | ❌ | ❌ | ❌ | 揮発無効は未実装 |
| じゅうなん | まひ状態を防ぐ | ON_BEFORE_APPLY_AILMENT | じゅうなん | ✅ | ✅ | ❌ | test_ability.py |
| みずのベール | やけど状態を防ぐ | ON_BEFORE_APPLY_AILMENT | みずのベール | ✅ | ✅ | ❌ | test_ability.py |
| マグマのよろい | こおり状態を防ぐ | ON_BEFORE_APPLY_AILMENT | マグマのよろい | ✅ | ✅ | ❌ | test_ability.py |
| どんかん | メロメロ・ちょうはつを防ぐ | ON_BEFORE_APPLY_AILMENT | どんかん | ❌ | ❌ | ❌ | 揮発無効は未実装 |
