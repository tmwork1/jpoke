# jpoke 改善チェックリスト

作成日: 2026-07-06
対象: ライブラリ全体（コード調査に基づく。`src/jpoke` 約42,000行、テスト関数2,692件時点）

優先度の目安:
- **高**: バグまたはバグの温床。放置すると誤動作・デグレの原因になる
- **中**: 開発効率・保守性・性能に効く。次の大きな作業の前に着手推奨
- **低**: あると良い。手が空いたときに

完了した項目は `- [x]` にする。対応しないと判断した項目は末尾の「対応しない項目」へ移す。

---

## 1. 正確性・バグリスク

- [x] **1-1. `Pokemon.__init__` の可変デフォルト引数 【高】**
  `src/jpoke/model/pokemon.py:56` — `move_names: list[MoveName] = ["はねる"]` は Python の典型的な落とし穴。
  デフォルトリストが全インスタンスで共有されるため、呼び出し先でこのリストが変更されると以降の全 Pokemon に波及する。
  `move_names: list[MoveName] | None = None` にして `__init__` 内で `["はねる"]` を生成する。

- [x] **1-2. `seed=0` が指定できない 【高】**
  `src/jpoke/core/battle.py:138` — `self.seed = seed or int(time.time())` は `seed=0` を falsy と判定して現在時刻に置き換える。
  再現テストやフーズで seed=0 を使うと非決定的になる。`seed if seed is not None else int(time.time())` に修正する。

- [x] **1-3. `MoveExecutor` のモニタリング属性の初期化漏れ 【高】**
  `src/jpoke/core/move_executor.py` — `move_power`（421行）と `move_category`（280行）は実行時に代入されるが、
  `__init__`（53-60行）と `reset_monitoring_flags()`（62-71行）のどちらにも含まれていない（`move_type` は含まれている）。
  - 技実行前に参照すると `AttributeError`
  - 前回の技の値が次の技実行に残留する（リセット漏れ）
  両メソッドに追加する。

- [x] **1-4. `resolve_speed_order` の「2匹前提」とタプル返却 【中】**
  `src/jpoke/core/speed_calculator.py:128-141` —
  - `speeds[0] == speeds[1]` は actives がちょうど2匹であることを暗黙に仮定している。片方がひんしで actives が1匹のときは `IndexError`
  - 素早さが異なる分岐では `zip(*paired)` の結果（タプル）をそのまま返しており、戻り値型 `list[Pokemon]` と不一致
  actives 数に依存しない実装にする。

- [x] **1-5. `get_active` の戻り型と None の不整合 【中】**（`Pokemon | None` に修正）
  `src/jpoke/core/battle.py:311-322` — 戻り型は `Pokemon` だが `PlayerState.active` は `None` になり得る。
  型チェッカーを導入すると多数の偽陰性/偽陽性の温床になる。`Pokemon | None` にするか、None でないことを保証する
  アサートを置いて呼び出し規約を明文化する。

- [x] **1-6. `foe()` / `actives` の暗黙の前提 【中】**（明示チェック＋日本語エラーメッセージ）
  `src/jpoke/core/battle.py:427-436` — `foe()` は `actives` リスト内の index に依存する。
  引数の mon が場にいない場合は `ValueError`（`.index` 失敗）で、エラーメッセージから原因が分かりにくい。
  明示的なチェックとメッセージを追加するか、player 経由の実装（`get_active(opponent(get_player(mon)))`）に置き換える。

- [x] **1-7. `DomainEvent` 発火時のハンドラリスト変異リスク 【中】**
  `src/jpoke/core/event_manager.py:128-131` — 通常イベントは `_sort_handlers` がコピーを返すためイテレーション中の
  登録/解除に耐えるが、`DomainEvent` は `self.handlers.get(event, [])` の生リストを直接イテレートする。
  ハンドラ内で `on`/`off` が呼ばれると `RuntimeError` や実行漏れになる。`list(...)` でコピーして統一する。

- [x] **1-8. `modify_hp` の `v`/`r` 併用仕様がコードで守られていない 【低】**（同時指定を ValueError に変更・r の範囲検証を追加）
  `src/jpoke/core/battle.py:531-555` — docstring に「同時指定時は r が優先」「r != 0 なら v も有限」とあるが検証がない。
  `assert` または明示的なエラーで契約を守らせる。

- [x] **1-9. `Handler.subject_spec` の検証タイミング 【低】**（ハンドラ名入りの検証を追加）
  `src/jpoke/core/handler.py:54-57` — `subject_spec.split(":")` が不正な文字列だと登録時ではなく
  `__post_init__` の unpack で `ValueError` になるが、メッセージに handler 名が含まれず特定しにくい。
  検証を入れて「どのハンドラの spec が不正か」を出す。

- [x] **1-10. コメントの誤字 【低】**
  `src/jpoke/core/move_executor.py:289,318` — 「かやたぶり」→「かたやぶり」（2箇所）。
  検索性（grep で「かたやぶり」を探したとき）に実害がある。

---

## 2. アーキテクチャ・設計

- [x] **2-1. deepcopy / update_reference の手動列挙の重複 【高】**（`update_reference` を持つ属性の自動検出に変更。option/test_option も deepcopy 対象化、ポケモン間参照の自動付け替えも追加）
  `Battle.__deepcopy__`（battle.py:196-220）の `keys_to_deepcopy` リスト、`_update_reference`（230-249行）の
  呼び出し列挙、各マネージャーの `__deepcopy__`/`update_reference` 定型文が全て手書きで三重管理になっている。
  **新しいマネージャーやフィールドを追加したとき、列挙し忘れるとコピーが浅くなり、木探索でコピー間の状態が
  共有される「静かなバグ」になる**（このクラスのバグは fuzz でしか見つからない）。
  - マネージャー登録を1つのレジストリ（`dict[str, Manager]`）に集約し、deepcopy / update_reference / 初期化を機械的に回す

- [x] **2-2. `Battle` の God object 化 【中】**（方針を決定し Battle docstring と CLAUDE.md に明文化: 外部APIは Battle 経由・マネージャー直呼びは内部のみ）
  `battle.py` は17個のマネージャーを保持し、大半のメソッドが単純な委譲（`run_move`, `judge_winner`,
  `resolve_speed_order`, `change_ability` など）。同じ操作に `battle.run_move()` と
  `battle.move_executor.run_move()` の2つの入口があり、どちらが正か曖昧になる。
  方針を決めて統一する（例: 外部 API は Battle 経由のみ、内部は manager 直呼びのみ）。

- [x] **2-3. `Pokemon` への用途特化フラグの増殖 【中】**（`memory` スコープ付きメモリを導入し6フラグを移行。既存APIはプロパティで互換維持）
  `model/pokemon.py:105-120` — `stat_lowered_this_turn`（うっぷんばらし用）、`failed_or_immobile_last_turn`
  （やけっぱち用）、`acted_since_switch_in`（であいがしら用）、`pp_consumed_moves`（とっておき用）…と、
  個別の技のためのフラグが増え続けている。さらに `reset_on_switch_in/out/turn_state` のどれでリセットするかを
  毎回正しく選ぶ必要があり、リセット漏れが繰り返し起きる構造。
  「ターン寿命」「登場中寿命」「バトル寿命」のスコープ付きメモリ（`mon.memory["turn"]["..."]` のような辞書＋
  一括クリア）に寄せると、新規フラグ追加時のリセット漏れが構造的になくなる。

- [x] **2-4. コアにハードコードされたドメイン知識 【中】**（ばんのうがさは ON_CHECK_WEATHER_IMMUNE イベント＋アイテムハンドラに移行。音技・粉技は「フラグから導出される汎用ルール」のため個別技への複製はせず、意図をコアのコメントに明記）
  イベント駆動が原則なのに、以下がコア側に直書きされている:
  - `battle.py:338-357` `weather_for()` — ばんのうがさの判定
  - `move_executor.py:337-352` — くさタイプの粉技無効
  - `move_executor.py:239-241` — 音技のみがわり貫通
  少数なら実害は小さいが、「例外はコアに直書きしてよい」という前例になり、増えるとイベントの優先順が
  `.internal/spec/turn.md` と一致しなくなる。ハンドラ化する

- [x] **2-5. `"role:side"` 文字列ベースのロール解決 【低】**（Handler 登録時と resolve_role の両方で検証を追加）
  `context.py:43-59` / `handler.py:54-57` — `getattr(self, role)` による解決は typo が実行時まで発覚しない。
  `RoleSpec` が Literal 型ならばかなり守られているが、`resolve_role` に来る spec の検証がない。
  NamedTuple 化（`Spec(role, side)`）か、少なくとも不正 role 名で即例外にする。

---

## 3. パフォーマンス

- [x] **3-1. `player_states` プロパティが毎回 dict を生成 【中】**（`__init__` で構築・deepcopy 時に再構築するキャッシュに変更）
  `battle.py:297-300` — `player_states` はホットパス（`resolve_action_order`, `has_interrupt` 等）から
  頻繁に参照されるが、呼び出しごとに zip + dict 内包を実行する。プレイヤーは固定なので
  `__init__` で構築してキャッシュできる（deepcopy 時の再構築だけ注意）。

- [x] **3-2. `calc_damages` の16乱数全計算 【低】**（調査の結果、対応不要と判断 → 「対応しない項目」参照）

---

## 4. データ管理

- [x] **4-1. `data/move.py` 9,082行の単一ファイル 【中】**（短期案を実施。`src/jpoke/data/moves/` パッケージを新設し、734件の技データを あ行/か行/さ行/た行/な行/は行/ま行/や行/ら行/わ行 + 記号・英数字の11ファイルに機械分割。`data/move.py` は分割モジュールを `**dict展開` で統合するだけの薄いファイル（約55行）に縮小。`from jpoke.data import MOVES` / `from jpoke.data.move import MOVES` の互換は維持。`scripts/sort_data/sort_moves.py` を分割後レイアウト対応に全面書き換え（行ごとの `--check` 対応込み）。`scripts/generate_literals/generate_move_literal.py` も dict 展開を再帰的に解決するよう修正（分割前提でないと `MOVES辞書に文字列以外のキーがあります` で落ちていた）。長期案（JSON/TOML化）は対応しない — ハンドラ関数参照がPythonオブジェクトのため大規模な設計変更が必要になり費用対効果が見合わないと判断）
  技データ718件が1ファイルの Python リテラルで、編集・レビュー・import 時間の全てでコストが高い。
  - 短期: あ行/か行…でファイル分割（`sort_moves.py` の分割対応が必要）
  - 長期: 数値・フラグ等の宣言的データを JSON/TOML に出し、ハンドラ参照だけ Python に残す。
    データの diff レビューが楽になり、外部ツール（乱数調整・ダメ計算機）からの再利用も可能になる

- [x] **4-2. `flags` が生 `set[str]` 【中】**（型注釈 `set[MoveFlag]` / `set[AbilityFlag]` は既に存在していた。実行時検証として `tests/test_data_integrity.py` を追加し、未定義フラグを検出できるようにした）
  `MoveData(flags={"contact", "non_negoto", ...})` — フラグ名の typo（`"non_negoto"` vs `"non_onnen"` 等）が
  実行時にも検出されず、単に「フラグが立っていない」扱いで静かに間違う。
  `.loop/review_results/set[MoveFlag]にする.ok` が存在するので既に認識済みと思われるが、
  `MoveFlag` の Literal 型 + `frozenset[MoveFlag]` にすれば型チェッカーで検出できる。

- [x] **4-3. マジックナンバー 【低】**（`utils/constants.py` に `PP_INFINITE` を定義して置換）
  `pp=99999`（わるあがき・_こんらん）などの番兵値。`PP_INFINITE` のような定数にして意図を明示する。

- [x] **4-4. 五十音順の維持が手動スクリプト頼み 【低】**（`sort_handlers.py` / `sort_data/sort_{abilities,items,moves}.py` / `sort_tests.py` に `--check`（並び替え済みでなければ終了コード1、ファイル変更なし）モードを追加。`.pre-commit-config.yaml` を新設し、ruff チェックと各並び順チェックを local フックとして登録。既存ファイルのうち一部（test_copy.py 等）は現状既に整列済みでない箇所があるが、これは pre-commit 導入前からの既存差分であり本項目のスコープ外のため今回は手を付けない — 対象ファイルが次に変更された際にフックで検出される）
  `scripts/sort_handlers.py` / `sort_data/*` / `sort_tests.py` の実行はルール（CLAUDE.md）でしか強制されていない。
  pre-commit フック化（並びが崩れていたら fail）すれば、agent/人間どちらの作業でも順序崩れが混入しない。

---

## 5. ツールチェーン・品質保証

- [x] **5-1. CI がない 【高】**（`.github/workflows/test.yml` を新設。push/PR で ubuntu-latest + windows-latest × Python 3.10/3.12 のマトリクス、`pip install -e .` → pytest → ruff → mypy。ubuntu/3.12 の1ジョブのみ `--cov=jpoke --cov-report=term` 付き。`.github/workflows/nightly-fuzz.yml` を新設し、6-4 と合わせて対応）
  `.github/workflows` が存在しない。テスト2,692件・fuzz スクリプト・並び順スクリプトという資産があるのに、
  実行が手元と `.loop` 頼み。GitHub Actions で最低限:
  - push/PR 時: `pytest tests/`（Windows + Linux のマトリクスなら文字コード問題も検出できる）
  - 定期（nightly）: `scripts/fuzz_battle.py` / `tsfuzz_battle.py` を時間制限付きで実行し、失敗シードを artifact 化

- [x] **5-2. リンター・型チェッカー未設定 【高】**（pyproject.toml に ruff/mypy 設定を追加。ruff 全126指摘を解消 — 3.12専用構文・重複テスト定義・重複import・ループ変数によるモジュール名シャドウ等の実バグを含む。mypy は core 対象で段階導入中、残2件 → その後 core の実エラーが54件まで増加していたため `follow_imports = "silent"` を追加して core 外への追従エラーを黙殺するよう修正し、core 自身のエラーを全て解消（`mypy` エラー0を達成）。GameEffect.name 等が `str` を返す設計上、Literal 型に渡す箇所は `cast` で明示、Pokemon | None の実質非None箇所は既存の `assert ... is not None` 規約に倣って追加。field_manager.py の LSP 違反（tick_down のシグネチャ不一致）は ExclusiveFieldManager 側を `tick_down_current()` に改名して解消）
  ruff / mypy(pyright) の設定が一切ない。本プロジェクトは Literal 型（`MoveName`, `AbilityName` 等）へ既に
  投資しているのに、型チェッカーがなければその恩恵（技名 typo の静的検出など）をほぼ受けられていない。
  - `ruff` 導入（B006 が 1-1 の可変デフォルト引数を自動検出する）
  - `mypy --strict` は現状厳しいはずなので、`src/jpoke/core` から段階的に
  - 設定は `pyproject.toml` に集約

- [x] **5-3. パッケージメタデータの二重管理と誤記 【中】**（pyproject.toml に一本化、setup.cfg を削除。typo・メールアドレス・bdist_wheel を修正）
  `pyproject.toml` と `setup.cfg` の両方にメタデータがあり、内容が食い違っている:
  - author email: `tmtm.holmes@email.com`（pyproject、**誤記**）vs `tmtm.holmes@gmail.com`（setup.cfg）
  - description の typo: 「Japansese」「developent」（両ファイル共通）
  - `[bdist_wheel] universal = 1` は Python 2 両対応の名残で不要
  pyproject.toml に一本化し、setup.cfg はパッケージ探索設定のみ残す（か、それも pyproject へ移す）。

- [x] **5-4. 依存関係・開発依存が未宣言 【中】**（`[dependency-groups] dev` に pytest / pytest-cov / ruff / mypy を宣言。`uv lock` を実行し uv.lock を18パッケージで更新済み）
  `dependencies = []` は正しい（本体は依存ゼロ）が、pytest / coverage / ruff などの開発依存が
  どこにも書かれていない。`[dependency-groups]`（uv 流）または `[project.optional-dependencies] dev` に宣言する。
  `uv.lock` が126バイト（実質空）なのも、uv を使うなら整合させる。

- [x] **5-5. `py.typed` がない 【低】**（`src/jpoke/py.typed` を追加し package-data に登録）
  型ヒント付きライブラリとして配布するなら `src/jpoke/py.typed` を置き、
  `setup.cfg` の package_data に含める。

- [x] **5-6. `.env` が git 追跡されている 【低】**（`.env.example` に改名して追跡、ローカル `.env` は untracked で維持。pytest は `pythonpath = ["src"]` 設定で .env 非依存に）
  `.gitignore` に `.env` があるが、それ以前に追跡開始されたため現在も tracked。
  中身は `PYTHONPATH=src` 等で無害だが、「gitignore にあるのに tracked」という不整合は事故のもと。
  追跡を残すなら `.env.example` に改名して gitignore と整合させる。

- [x] **5-7. `.loop` 状態ファイルの git 管理 【低】**（`.loop/review_results/` を gitignore に追加し追跡解除。queue/state は tracked を維持）
  `.loop/` 配下の状態ファイル114件が tracked で、ループ実行のたびに大量の削除/変更が git status を汚す
  （現在も review_results の削除21件が未コミット）。作業キュー（queue/state）は tracked のままでよいが、
  `review_results/*.ok` のような使い捨てマーカーは gitignore するか、完了時にまとめてコミットする運用を決める。

---

## 6. テスト

- [x] **6-1. 巨大テストファイルの分割 【中】**（`tests/test_item.py`（273KB, 450関数/603テスト）を `tests/items/` に あ/か/さ/た/な/は/ま/やらわ + misc（非かな始まり）の9ファイルへ機械分割。`_dummy_move` ヘルパーは参照する `test_item_ta.py` にのみ複製。分割前後でテスト収集数（603件）が一致することを確認済み。`test_field.py`（63KB, 109テスト）と `test_lethal.py`（59KB, 75テスト）は test_item.py の1/4〜1/5規模で、既存の未分割ファイル（例: test_utils.py 13.9KB）と比べると大きいものの、test_item.py ほどの逼迫度ではないため今回は分割を見送り、test_item.py のみ分割した）
  `tests/test_item.py` が 273KB、`tests/test_field.py` が 63KB、`tests/test_lethal.py` が 59KB。
  abilities/ や moves_attack/ と同様にサブディレクトリ＋五十音分割する
  （`sort_tests.py` / `generate_test_list.py` は対応済みのはず）。編集時の context コストと
  テスト探索性の両方に効く。

- [x] **6-2. カバレッジ計測がない 【中】**（pyproject.toml に `[tool.coverage.run] source = ["src/jpoke"]` と除外設定を追加。`.github/workflows/test.yml` の ubuntu/3.12 ジョブでのみ `--cov=jpoke --cov-report=term` を有効化）
  2,692件のテストがどこを通っていないか分からない。`coverage.py` を導入し、
  特に `handlers/` の分岐カバレッジを見る。実装済みなのにテストが一切通らないハンドラ
  （登録ミス・subject_spec ミス）の検出にも使える。

- [x] **6-3. コピー健全性の自動テスト 【中】**（オブジェクトグラフ並行走査テストを追加。`recursive_copy` の set 非コピーと `contact_hitter` の旧 Battle 参照という実バグ2件を検出・修正）
  2-1 と対:「`Battle.copy()` 後に元と複製で状態が共有されていないこと」を全マネージャー・全 Pokemon 属性に
  ついて機械的に検証するテスト（属性を歩いて id 比較）。`tests/test_copy.py`（4.8KB）はあるが、
  新規属性の追加に自動追従する形（`vars()` を走査して mutable な共有を検出）へ強化すると 2-1 の保険になる。

- [x] **6-4. fuzz の常設化 【低】**（`.github/workflows/nightly-fuzz.yml` を新設。毎日UTC18時に `fuzz_battle.py --search`（500件）と `tsfuzz_battle.py --search`（100件）を各15分のタイムアウト付きで実行し、開始シードは実行日から決定的に算出。失敗時は `.loop/fuzz_failures/` `.loop/tsfuzz_failures/` を artifact としてアップロードしジョブを失敗させる。issue 自動化は見送り — 現状の artifact 化で再現コマンドが手元に残るため、まずはここまでとする）
  `fuzz_battle.py` / `tsfuzz_battle.py` と `test_fuzz_regressions.py` の回帰蓄積は良い仕組み。
  CI（5-1）の nightly に組み込み、新規失敗シードを自動で issue 化できるとさらに良い。

---

## 7. ドキュメント・API

- [x] **7-1. README の全面的な陳腐化 【高】**（README.md を全面書き直し。CLAUDE.md のアーキテクチャ表・ディレクトリ構成をベースに、存在しないファイル参照を除去。コード例は実際に実行して動作確認済み（`Battle`/`Player`/`Pokemon` の生API例、`tests.test_utils` 利用例の2種）。種数は `jpoke.data` の実行時辞書サイズ（内部用の空/`_`始まりエントリを除く）から取得: 特性310・アイテム247・技733・揮発性状態66・状態異常7・場の効果31）
  `README.md` は現状と大きく乖離している:
  - 存在しないファイルを参照: `core/turn.py`, `core/event.py`, `core/speed.py`, `core/switch.py`,
    `model/ability.py`（実在するが説明と乖離）, `tests/run.py`, `tests/test_ability.py`, `progress/*.md`（実際は `.internal/progress/`）
  - コード例（いかく）が実 API と無関係（`イベントType.CHANGE_STAT_STAGE` は存在しない）
  - 種数（特性299種など）が古い可能性
  外部に見せる最初のファイルなので、現アーキテクチャ（CLAUDE.md の表が正確）をベースに書き直す。

- [x] **7-2. ターゲット世代の記述不一致 【中】**（README.md に「対象範囲」節を新設し、「対象はポケモンチャンピオンズのシングルバトルのみ。仕様ソースは第9世代（SV）を基本とし、チャンピオンズ側でルールが異なる場合はそちらを優先」と1箇所で定義。CLAUDE.md のプロジェクト概要はこの定義を README 側に委譲する形に変更）
  README は「第9世代（SV）を参照」、CLAUDE.md は「ポケモンチャンピオンズのシングルバトルをターゲット」。
  両者の関係（チャンピオンズ準拠だが仕様ソースは SV、等)を1箇所で定義し、他方から参照する。

- [x] **7-3. `print` ベースのログ出力 【低】**（`Battle.get_log_lines(turn=None) -> list[str]` を新設し `print_logs` はその結果を print するだけの薄いラッパーに変更。`Pokemon.show()` も同様に `render_info() -> str` を新設し `show()` はラッパー化。両 API とも互換維持）
  `battle.py:698-711` `print_logs` / `model/pokemon.py:807`。ライブラリとしては `logging` か、
  `render()` 済み文字列のリストを返す API にして出力先を呼び出し側に委ねる方が使いやすい。

- [x] **7-4. 例外の粒度 【低】**（`src/jpoke/exceptions.py` を新設。`JpokeError` を基底に `InvalidCommandError` / `InvalidPhaseError` / `PokemonNotFoundError` / `InvalidStatModificationError` を定義し、全て `ValueError` を多重継承して後方互換を維持。`battle.py` の `step()`（Invalid command / No commands）と `get_available_commands()`（Invalid phase）を置換。`step()` の commands=None かつ非新規ターン時に `commands.get()` で AttributeError になり得た潜在バグも合わせて明示的な `InvalidCommandError` に修正）
  エラーがほぼ素の `ValueError`。`InvalidCommandError` / `PokemonNotFoundError` 等のドメイン例外を
  `jpoke.exceptions` に定義すると、bot 開発側（このライブラリの想定ユーザー）が except しやすくなる。

- [x] **7-5. `Pokemon.hp` 直接代入禁止ルールのコードによる強制 【低】**（実行時 property 化はテストのセットアップ代入を壊すため見送り。代わりに `tests/test_code_conventions.py` を新設し、src/jpoke 配下の `.hp = ` 直接代入を静的走査で検出。許可リストは model/pokemon.py・core/status_manager.py に加えて、致死率計算用のスクラッチ操作である core/lethal.py も追加。既存違反は全て正当な例外だったため実装修正は不要）
  CLAUDE.md の規約「`hp` へ直接代入禁止」は現状レビュー頼み。`hp` を property 化し、
  setter で `modify_hp` 経由以外の代入を禁止（またはデバッグモードで警告）すれば規約が構造化される。

---

## 8. シミュレーション品質（bot/探索用途）

- [x] **8-1. 乱数ストリームの共有 【中】**（`copy(reseed=True)` を追加。派生シードは決定的で元の乱数系列を消費しない）
  `Battle.random` は単一 `Random`。`copy()` した複数の探索枝が同一系列の続きを引くため、
  枝同士の乱数が完全相関する（期待値評価としては歪む場合がある）。
  探索用途では「コピー時に子 seed を派生させる」オプション（`copy(reseed=True)` 等）を用意する。

- [x] **8-2. 観測（情報隠蔽）の漏洩テスト 【低】**（`tests/test_observation.py` を新設。非公開のアイテム・特性・技（一部のみ公開の混在ケース含む）・テラスタイプ・性格・努力値が observer 視点で隠蔽されること、および observer 自身の情報は隠蔽されないことを検証。6件のテストを追加）
  `build_observation` / `observation_builder` は bot 対戦の公平性の要。
  「observer 視点のコピーに相手の非公開情報（未開示の技・アイテム・テラスタイプ等）が含まれない」ことを
  属性走査で機械的に検証するテストがあると、新属性追加時の漏洩を防げる。

---

## 対応しない項目

判断済みのため着手不要。再検討する場合はこのセクションから戻す。

- **（旧 3-1）`emit` のたびにハンドラを素早さソート** — 厳密性を優先し、対応しない。
  `event_manager.py:168-185` — イベント発火ごとに全登録ハンドラの `calc_effective_speed` を呼ぶコストがあるが、
  キャッシュ導入は無効化タイミング（ランク変化・アイテム/特性変化・天候変化）の管理を誤ると挙動の正確性を損なうため見送り。

- **（旧 3-3）木探索向けコピー戦略（undo ログ方式等）** — 対応しない。
  `Battle.copy()` は `fast_copy` 導入済みの deepcopy ベースを維持する。

- **（3-2）`calc_damages` の16乱数全計算** — 調査の結果、対応しない。
  コストの大半はループ外のイベント発火（1回のみ実行）であり、16値ループ自体は乗算5回×16の
  軽微な演算。単一乱数パスの追加はコード分岐を増やすだけで得るものが小さい。

---

## 推奨着手順

1. **即日級（小さくて効果大)**: 1-1 可変デフォルト / 1-2 seed=0 / 1-3 モニタリング属性 / 1-10 誤字
2. **基盤（1〜2日)**: 5-2 ruff+mypy 導入 → その過程で 1-4〜1-7 の型不整合が芋づるで直る / 5-1 CI / 5-3 メタデータ一本化
3. **構造（継続的)**: 2-1 コピー機構の自動化＋6-3 コピー健全性テスト / 2-3 スコープ付きメモリ / 4-1 データ分割
4. **性能（プロファイル後)**: 3-1 player_states のキャッシュ / 3-2 ダメージ乱数の計算削減
5. **対外整備**: 7-1 README 書き直し / 7-2 ターゲット定義の一本化
