# test_command

テスト数: 17

- [x] GIGAMAXコマンド_明示的に渡すとわるあがきになる
- [x] GIGAMAXコマンド_行動候補に含まれない
- [x] ZMOVEコマンド_明示的に渡すとわるあがきになる
- [x] ZMOVEコマンド_行動候補に含まれない
- [x] is_struggle_only_FORCEDが優先される場合はFalse
- [x] is_struggle_only_かなしばりで全ての技が封じられた場合はTrue
- [x] is_struggle_only_こだわりで変化技に固定されちょうはつを受けた場合はTrue
- [x] is_struggle_only_ちょうはつで変化技しか使えない場合はTrue
- [x] is_struggle_only_交代可能な控えがいても正しくTrueを返す
- [x] is_struggle_only_技コマンドがある場合はFalse
- [x] is_struggle_only_技のPPが尽き交代先もいない場合はTrue
- [x] is_switch_プロパティとしてコマンド種別ごとに真偽を返す
- [x] is_type_Noneを渡すと偽を返す
- [x] is_type_anyを指定すると全てのコマンドが真になる
- [x] is_type_moveを指定すると技系コマンドのみ真になる
- [x] is_type_switchを指定すると交代コマンドのみ真になる
- [x] ちょうはつ_コマンド選択後に受けても行動前ならブロックされる
