# test_tree_search_framework

テスト数: 15

- [x] configure_simが各分岐でsim_step実行前に呼ばれる
- [x] estimate_opponentを指定すると推定情報から探索が継続される
- [x] evaluate_commandsがmax_nodesを無視して全合法手を評価する
- [x] evaluate_commandsが非破壊的に評価値一覧を返す
- [x] evaluateの既定実装がget_team経由で対戦中の実データを反映する
- [x] evaluate関数が例外を投げてもsearchingフラグは解除される
- [x] fallbackに独自関数を指定するとそれが使われる
- [x] max_nodesでノード数上限が機能する
- [x] max_plies2でネストしたsimでも全階層のseedが重複しない
- [x] max_plies2で相手の未公開技が2手目の分岐にも現れない
- [x] reseedTrueにより兄弟ノード間でsimの乱数系列が独立する
- [x] とんぼがえり使用時に相手のベンチが公開済みでもValueErrorにならない
- [x] 探索中に割り込み交代が発生してもフォールバックで完了する
- [x] 有利な技を選択する
- [x] 相手の合法手が未公開の場合fallbackに委譲される
