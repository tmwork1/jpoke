# test_stats

テスト数: 29

- [x] add_pokemonでevsとivsを省略すると既定値のまま
- [x] add_pokemonでevsをdict指定すると指定ステータスのみ反映される
- [x] add_pokemonでevs指定時に生成直後のhpが満タンで追従する
- [x] add_pokemonでivsをdict指定すると指定ステータスのみ反映される
- [x] ステータス実数値設定_set_statsで6項目に満たない辞書を渡すと他のステータスは変化しない
- [x] ステータス実数値設定_set_statsでキー順が典型順と異なる辞書でも正しく反映される
- [x] ヌケニンはレベル個体値努力値に関わらずHP実数値が常に1固定(level=1, iv_hp=0, ev_hp=0)
- [x] ヌケニンはレベル個体値努力値に関わらずHP実数値が常に1固定(level=43, iv_hp=31, ev_hp=0)
- [x] ヌケニンはレベル個体値努力値に関わらずHP実数値が常に1固定(level=50, iv_hp=0, ev_hp=32)
- [x] ヌケニンはレベル個体値努力値に関わらずHP実数値が常に1固定(level=100, iv_hp=31, ev_hp=32)
- [x] 個体値_set_ivsでdict指定すると指定ステータスのみ更新し未指定分は既存値を維持する
- [x] 個体値_set_ivsでdict指定後にステータスが再計算される
- [x] 個体値_set_ivsでlist指定すると全体を置き換える
- [x] 個体値_set_ivsのdict部分更新が他インスタンスのivsに影響しない
- [x] 努力値_keep_ratioを指定するとHP割合が維持される
- [x] 努力値_resetを指定すると被ダメージ状態でも満タンになる
- [x] 努力値_set_evs_atで単一インデックス設定
- [x] 努力値_set_evsでdict指定すると指定ステータスのみ更新し未指定分は既存値を維持する
- [x] 努力値_set_evsで設定と取得
- [x] 努力値_set_evsのdict部分更新が他インスタンスのevsに影響しない
- [x] 努力値_ステータス再計算に反映される
- [x] 努力値_ダメージ中にset_evsすると被ダメージ絶対量が維持される
- [x] 努力値_未ダメージ状態でset_evsしてもhpは満タンのまま
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=0, effort_sv=0)
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=1, effort_sv=4)
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=2, effort_sv=12)
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=3, effort_sv=20)
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=31, effort_sv=244)
- [x] 努力値変換_チャンピオンズからSV(effort_chmp=32, effort_sv=252)
