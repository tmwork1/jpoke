# test_query

テスト数: 14

- [x] can_use_last_resort_他の技をすべて使用済みならtrue
- [x] can_use_last_resort_未使用技が残っている場合はfalse
- [x] get_forced_move_name_あなをほるで固定技名を返す
- [x] get_forced_move_name_固定されていない場合はnone
- [x] has_available_bench_とらわれ状態でも控えの生存で判定する
- [x] has_available_bench_控えが全滅していればfalse
- [x] is_first_actor_行動順に基づき先攻を判定する
- [x] is_first_actor_行動順未確定ならnone
- [x] is_floating_ひこうタイプはtrue
- [x] is_hazard_immune_あつぞこブーツでtrue
- [x] is_nervous_相手のきんちょうかんでtrue
- [x] is_second_actor_行動順に基づき後攻を判定する
- [x] is_trapped_ゴーストタイプはにげられないでも逃げられる
- [x] is_trapped_にげられないでtrue
