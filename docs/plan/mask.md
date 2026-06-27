# 情報の隠蔽

## 相手のコマンドの隠蔽フロー

1. 相手の開示情報から予測手リスト `predictable_commands`を作成する。
2. 合法手リスト`player_state.legal_commands`を`predictable_commands`に置き換える。
3. コマンドが予約済みなら`player_state.reserved_command`を空にし、`predictable_commands`からひとつ選ぶ。

`predictable_commands`が空で選べなくなるケース
case 1. 開示されている相手のactiveの技と交代可能ポケモンがない
case 2. 同時死に出しでベンチが非公開

### 行動選択時
予測手 = 