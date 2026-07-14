# test_copy

テスト数: 9

- [x] copy_logsFalseでdeepcopy中に例外が発生しても複製元のログが復元される
- [x] copy_logsFalseで複製元のログが変更されずかつ複製先への書き込みが波及しない
- [x] copy_logsFalseで複製先のログが空になる
- [x] copy_logsTrueで従来通りログの全履歴が引き継がれる
- [x] mon
- [x] terrain
- [x] weather
- [x] コピー後に可変状態が共有されない
- [x] 木探索用の観測でswitchフェーズ中の相手コマンドがrequired_command_typeでフィルタされる
