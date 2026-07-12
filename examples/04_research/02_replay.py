"""jpoke で学べること: 対戦の記録・再生（リプレイ）機能一式。

対戦を最後まで進めて `Battle.build_replay_data()` で「チーム＋シード＋選出＋
コマンド列」を記録し、`replay_battle()` でその記録から同じ展開の対戦をそのまま
再生する。`ReplayPlayer` は記録済みの選出・コマンドを発生順に払い出すだけの
プレイヤーで、方策判断は一切行わない。「興味深い対戦を記録して後で解析する」
という戦術研究ユースケースの入口。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.core.replay import replay_battle


def main() -> None:
    player1 = Player("Player 1")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()
    # 手動でstep()するループの定型は01で学んだので、ここではplay_out()で一括して進める
    winner = battle.play_out(max_turns=100)
    print(f"元の対戦の勝者: {winner.username if winner else '引き分け（ターン上限）'}（{battle.turn}ターン）")

    # build_replay_data() は対戦の途中でも呼べるが、ここでは決着後に呼ぶ
    replay_data = battle.build_replay_data()

    # to_dict()/from_dict() で辞書化・復元できる。json.dumps()/json.loads() を
    # 挟めばファイル保存や別プロセスへの受け渡しもできる
    serialized = replay_data.to_dict()
    restored = type(replay_data).from_dict(serialized)

    replayed_battle = replay_battle(restored)

    replayed_winner = replayed_battle.winner
    print(
        f"再生した対戦の勝者: "
        f"{replayed_winner.username if replayed_winner else '引き分け（ターン上限）'}"
        f"（{replayed_battle.turn}ターン）"
    )
    print("同じ展開が再現されているはず（勝者・ターン数が元の対戦と一致する）")

    # 試してみよう: serialized を json.dumps() でファイルに保存し、別プロセスで
    # json.load() → from_dict() → replay_battle() すると、対戦の記録・共有・
    # 後日の再解析ができる


if __name__ == "__main__":
    main()
