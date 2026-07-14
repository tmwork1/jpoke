# test_form

テスト数: 6

- [x] set_form_hp_policyでresetを指定すると被ダメージ状態でも満タンになる
- [x] set_form_keep_absoluteが既定で被ダメージ絶対量が維持される
- [x] set_form_set_default_abilityにTrueを指定すると変更先の先頭特性にリセットされる
- [x] set_form_set_default_abilityを指定しない場合は特性が維持される
- [x] set_form_同じフォルムを指定すると何も変更されずFalseが返る
- [x] set_form_異なるフォルムを指定すると種族値タイプが切り替わりTrueが返る
