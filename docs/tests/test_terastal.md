# test_terastal

テスト数: 11

- [x] terastallize_戻り値はNone
- [x] グラススライダー_テラスタルで威力60に底上げされる
- [x] ステラタイプ補正(tera_type=ステラ, move=でんきショック, expected_initial=8192, expected_after=6144)
- [x] ステラタイプ補正(tera_type=ステラ, move=ひのこ, expected_initial=4915, expected_after=4096)
- [x] 威力底上げ(move_name=でんきショック, tera_type=でんき, expected=60)
- [x] 威力底上げ(move_name=でんきショック, tera_type=ほのお, expected=40)
- [x] 威力底上げ(move_name=でんこうせっか, tera_type=ノーマル, expected=40)
- [x] 威力底上げ(move_name=にどげり, tera_type=かくとう, expected=30)
- [x] 攻撃側タイプ補正計算(tera_type=でんき, move=でんきショック, expected=8192)
- [x] 攻撃側タイプ補正計算(tera_type=ほのお, move=ひのこ, expected=6144)
- [x] 攻撃側タイプ補正計算(tera_type=ほのお, move=でんきショック, expected=6144)
