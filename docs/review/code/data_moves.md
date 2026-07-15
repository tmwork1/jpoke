# コードレビュー — data/moves/

日付: 2026-07-12
対象: `src/jpoke/data/moves/`
（`move_a.py`, `move_ka.py`, `move_sa.py`, `move_ta.py`, `move_na.py`, `move_ha.py`,
`move_ma.py`, `move_ya.py`, `move_ra.py`, `move_wa.py`, `move_symbol.py`。
`__init__.py` は空ファイルのため対象外。合計約8000行、`MOVES_<行>` 辞書11個・
技エントリ約850件）
観点:
1. 一般的な品質観点（構造の一貫性、コピペミスの兆候、ファイル分割基準の逸脱、
   データ定義への不要なロジック混入）
2. 変数・関数・辞書キー名の一貫性と妥当性（フィールド名の統一、ハンドラ参照名の
   命名パターン、技系統ごとの属性表現の統一、五十音順の遵守）

前回の総合レビュー（`docs/review/code/index.md`、2026-07-05付）は `data/moves/` を
対象範囲に含んでいなかったため、本レビューが本ディレクトリに対する初回レビューとなる。

---

## 総論

`data/moves/` は `MoveData`（`src/jpoke/data/models.py:55-68`）のフィールド
（`type`/`category`/`pp`/`power`/`accuracy`/`priority`/`critical_rank`/`target`/
`flags`/`multi_hit`/`handlers`/`lethal_handlers`）を五十音行ごとに11ファイルへ
分割して定義する、純粋なデータ定義層である。全ファイルを通読した結果、以下が
確認できた。

- **フィールドの並び順・命名は約850エントリを通じて完全に統一されている**。
  `type → category → pp → power → accuracy → priority → critical_rank → target
  → flags → multi_hit → handlers → lethal_handlers`（存在するフィールドのみ、
  この相対順序）から外れる箇所は1件も見つからなかった。キー名の表記ゆれ
  （大文字小文字・別名等）も皆無。
- **五十音順は`scripts/sort_data/sort_moves.py --check`で機械的に「整列済み」と
  確認できた**（実行結果: `OK: 11 ファイルとも整列済み`）。手読みでも違反は
  見つからなかった。
- ハンドラ参照（`h.`/`ha.`/`hs.`/`l.`）のインポートエイリアスは全11ファイルで
  統一されており、`lethal_handlers` を持たないファイル（`move_na.py`,
  `move_wa.py`, `move_ya.py`）では `LethalEvent`/`LethalHandler`/`l` の
  importが省かれ、未使用importも存在しない。
- データ定義層に本来あるべきでない制御ロジックの混入は見つからなかった
  （`handlers` には常に `Handler`/`MoveHandler` オブジェクトの登録のみが
  置かれ、条件分岐等は `handlers/*.py` 側に閉じている）。

その一方で、**技データの「PP の根拠」を説明するコメントが、直前に発生した
ドキュメントのファイル名変更に追随できておらず、8ファイル13箇所で存在しない
パスを参照している**（重大な指摘1件目）。またスワップ系技4兄弟のうち1つ
（`ハートスワップ`）だけが、同じ「ハンドラ命名パターン」を持ちながら
`accuracy`/`flags` の値が兄弟技と食い違っており、自身の系統の仕様書
（`docs/spec/moves/パワースワップ.md`）が明記する必中要件に反している疑いが
強い（重大な指摘2件目）。これらは両方とも「命名・参照の一貫性」を手がかりに
発見した実質的な不具合であり、今回の重点観点が有効に機能した例といえる。

---

## 重大な指摘

### CRIT-1: PP根拠コメントが13箇所で「存在しないファイル」を参照している

**ファイル**: `move_na.py:439`, `move_ta.py:308,1327,1343,1645`, `move_ra.py:349`,
`move_wa.py:21`, `move_ya.py:107`, `move_ha.py:783,1372,1483`, `move_ma.py:420,809`

PPの根拠を示すコメントが `move_list.txt`（`src/jpoke/data/ps-champ-ja/moves.json` 等の
表記ゆれあり）を参照しているが、このファイルは2026-07-11のコミット
`01d217d7`（`fix: src/jpoke/data/ps-champ-ja/moves.json との技データ不一致を修正`）で
`src/jpoke/data/ps-champ-ja/moves.json` → `src/jpoke/data/ps-champ-ja/moves.json` に**リネーム済み**
であり、`move_list.txt` は現在リポジトリ上に実在しない。

```python
# move_wa.py:21（最も古い形跡を残す例）
pp=12,  # champions基準（src/jpoke/data/ps-champ-ja/moves.json 970行目）。Gen9本家は10
```

この行はファイル名の失効に加え、「970行目」という行番号までハードコードして
おり、`.txt` → `.md` へのフォーマット変更で行番号の対応関係自体も無意味に
なっている。他の12箇所も同様に存在しないパスを参照しており、今後このコメントを
頼りに実際の一次情報を確認しようとした開発者は空振りする。ユーザーの
CLAUDE.md 運用メモにも「技PPは `champions/move_list.txt` が正」という記載が
残っており、リネームの影響が `data/moves/` 側のコメント・関連ドキュメントの
双方に波及していないことがうかがえる。13箇所すべてを `src/jpoke/data/ps-champ-ja/moves.json`
参照に一括置換すべき（行番号を含む1箇所は行番号表記自体の削除も検討する）。

該当13箇所の内訳:

| ファイル:行 | 現在のコメント |
|---|---|
| move_na.py:439 | `champions基準（move_list.txt）。Gen9本家は15` |
| move_ta.py:308 | `チャンピオンズ基準（src/jpoke/data/ps-champ-ja/moves.json）。第9世代本家基準は10` |
| move_ta.py:1327 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。Gen9本家は10` |
| move_ta.py:1343 | `championsのPP圧縮則により導出（move_list.txtに単独項目なし）。Gen9本家は40` |
| move_ta.py:1645 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。旧値25はSV本家基準の移行漏れ。` |
| move_ra.py:349 | `チャンピオンズ基準（src/jpoke/data/ps-champ-ja/moves.json）。第9世代本家基準は10` |
| move_wa.py:21 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json 970行目）。Gen9本家は10` |
| move_ya.py:107 | `champions_move_list.txtに記載なし。第9世代の値を採用` |
| move_ha.py:783 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。Gen9本家は15` |
| move_ha.py:1372 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。旧値10はSV本家基準の移行漏れ。` |
| move_ha.py:1483 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。旧値25はSV本家基準の移行漏れ。` |
| move_ma.py:420 | `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。旧値5はSV本家基準の移行漏れ。` |
| move_ma.py:809 | `champions/move_list.txtに記載なし。Gen9本家基準の値をそのまま採用` |

### CRIT-2: `ハートスワップ`（move_ha.py:404-414）の `accuracy`/`flags` が兄弟技・自系統の仕様書と食い違っている

**ファイル**: `src/jpoke/data/moves/move_ha.py:404-414`

```python
"ハートスワップ": MoveData(
    type="エスパー",
    category="status",
    pp=10,
    accuracy=100,
    handlers={
        Event.ON_STATUS_HIT: h.MoveHandler(
            hs.ハートスワップ_swap_ranks,
        ),
    }
),
```

同じ「ランク入れ替え」系統の3技と比較する。

```python
# move_ka.py: ガードスワップ
accuracy=None,  # 必中
# マジックコートで跳ね返されず、みがわりを貫通する
flags={"unreflectable", "bypass_substitute"},

# move_ha.py: パワースワップ
accuracy=None,  # 必中
# マジックコートで跳ね返されず、みがわりを貫通する
flags={"unreflectable", "bypass_substitute"},

# move_sa.py: スピードスワップ
accuracy=None,  # 必中
# マジックコートで跳ね返されず、みがわりを貫通する
flags={"unreflectable", "bypass_substitute"},
```

`ハートスワップ` はハンドラ名こそ `hs.ハートスワップ_swap_ranks` と兄弟技の
`hs.パワースワップ_swap_ranks` 等と同じ命名パターンに従っているにもかかわらず、
`accuracy=100`（`None` ではない）で `flags` が未設定という異質な値になっている。

これは単なる命名の不統一にとどまらない。`docs/spec/moves/パワースワップ.md`
の「判定」節（46行目）には次の明記がある。

> 必中技: `accuracy=None` を設定する必要がある（`accuracy=100` のままだと
> ON_MODIFY_ACCURACY 経由でランク補正（回避率上昇等）の影響を受けてしまい、
> 必中にならない）

さらに同ファイル「備考」節（88-89行目）は

> ガードスワップ（ぼうぎょ・とくぼうの**ランク**入れ替え）、パワースワップ
> （こうげき・とくこうの**ランク**入れ替え）、ハートスワップ（全ステータスの
> **ランク**入れ替え）という整合関係がある。

と、`ハートスワップ` を含む3技が同一パターンに従うべきことを明示的に述べて
いる。加えて「イベントフロー」節（77行目）でも実装方式について
「`ガードスワップ`・`ハートスワップ` と同一パターン」と名指ししている。

つまり `ハートスワップ` の `MoveData` は自身の兄弟技の仕様書が定義する契約に
違反しており、相手の回避率が上昇している場面では本来必中のはずの技が外れる
可能性がある（`flags` 未設定によりまもる・マジックコート・みがわりの扱いも
兄弟技と異なる可能性が高い）。`accuracy=None,  # 必中` と
`flags={"unreflectable", "bypass_substitute"}` を追加すべき
（`src/jpoke/` 配下の変更は本レビューの制約により実施していない。修正候補として
記録する）。

---

## 中程度の指摘

### ISSUE-1: 同一事実を説明するコメントが7通り以上の異なる文面で表記されている

**ファイル**: CRIT-1の表と同一13箇所

CRIT-1で指摘した「参照パスが存在しない」問題とは独立に、「PPがチャンピオンズ
基準でGen9本家と異なる」という同一の事実を説明するコメントの**文面そのもの**が
ファイルごとにばらついている。

- `champions基準（src/jpoke/data/ps-champ-ja/moves.json）。Gen9本家は10` （英語+カタカナ混在なし）
- `チャンピオンズ基準（src/jpoke/data/ps-champ-ja/moves.json）。第9世代本家基準は10` （全カタカナ + 「本家基準」という言い回し）
- `champions基準（move_list.txt）。Gen9本家は15` （`docs/`プレフィックス欠落）
- `championsのPP圧縮則により導出（move_list.txtに単独項目なし）。Gen9本家は40` （「PP圧縮則」という別概念の導入）
- `champions_move_list.txtに記載なし。第9世代の値を採用` （アンダースコアでパス風文字列を連結、他とは別記法）
- `champions/move_list.txtに記載なし。Gen9本家基準の値をそのまま採用（...Championsに記載のない技と同様）` （「Championsに記載」と大文字始まりの表記も混在）

同じ意味を表すコメントテンプレートが統一されていないため、grep等で「champions
基準のPP値」を機械的に洗い出すことが難しい。`# champions基準（docs/champions/
moves.md）: Gen9は<値>` のような単一テンプレートに統一し、CRIT-1の修正と
合わせて一括で書き直すことを推奨する。

### ISSUE-2: `ふくろだたき`（move_ha.py:917）の `multi_hit` のみ1行書式で他の約20件と体裁が異なる

**ファイル**: `src/jpoke/data/moves/move_ha.py:917`

```python
multi_hit={"min": 1, "max": 6, "check_hit_each_time": False, "power_sequence": ()},
```

`data/moves/` 全体で `multi_hit` を持つエントリは約20件あるが、この1件を除く
すべてが次の4行展開書式で統一されている（例: `move_sa.py:913-918` の
`すいりゅうれんだ`）。

```python
multi_hit={
    "min": 3,
    "max": 3,
    "check_hit_each_time": False,
    "power_sequence": (),
},
```

`scripts/sort_data/sort_moves.py` はエントリ内の空行除去は行うが、この種の
1行/複数行の書式差は矯正しない（実際 `--check` はこの状態のままでも
「整列済み」と判定する）。手作業での追加時に他エントリからのコピー元を誤った
か、行数の少なさから展開を省略したものと見られる。可読性の統一のため他の
`multi_hit` と同じ4行書式に揃えるべき。

### ISSUE-3: 複数技で共有される汎用ハンドラの命名規則が3パターンに分裂している

**ファイル**: `src/jpoke/data/moves/*.py`（`ha.` 参照全般）、
`src/jpoke/handlers/move_attack.py:55`

個別技専用のハンドラは一貫して `<技名>_<効果内容>`（例:
`アイアンテール_lower_defender_def`）という snake_case 命名で統一されている。
一方、2件以上の技から共有される汎用ハンドラは、次の3種の命名規則が並行して
使われている。

1. **完全な英語 snake_case**（技名を含まない）:
   `reduce_damage_in_double_battle`（59技で使用）, `apply_bind_to_defender`
   （9技）, `charge_into_volatile`（9技、二段技共通ヘルパー）,
   `gravity_restricted_fail`（7技）, `ohko_damage`（4技）,
   `level_fixed_damage`（2技）, `half_damage`（2技）, `on_blow_apply`/
   `on_blow_check_switch_target`/`blow`（各2技、ふきとばし・ほえる系）
2. **代表技の日本語名 + 英語動詞サフィックス**:
   `リチャージ_apply`（8技、はかいこうせん等の反動硬直技系統の代表として
   「リチャージ」という状態名を採用）, `あばれる_apply`（4技、
   げきりん・だいふんげき・はなびらのまい・あばれる自身が連続攻撃状態の
   代表技「あばれる」の名を借用）, `ソーラービーム_halve_power`（2技、
   ソーラーブレードがソーラービームの威力半減ロジックを共有）,
   `まもる系_連続使用失敗チェック`（9技、`系`サフィックスで「まもる系統」を
   明示する独自の記法）
3. **日本語の名詞句そのもの（アンダースコア区切りなし）**:
   `効果抜群時威力ブースト`（`move_a.py:191`のアクセルブレイク、
   `move_a.py:635`のイナズマドライブで使用）

3番目の `効果抜群時威力ブースト` は、他の汎用ハンドラや個別技ハンドラが
例外なく採用している「名詞_動詞句」のアンダースコア区切りに従っておらず、
1つの連続した名詞句になっている点で際立って異質である。汎用ハンドラの命名を
今後増やす際は、少なくとも「アンダースコア区切りを維持する」ことだけは
統一し、可能であれば英語/日本語のどちらかの命名規則にそろえることが望ましい
（両方式の混在自体は「技名を借用できる代表技があるかどうか」で説明がつくため
許容範囲内だが、`効果抜群時威力ブースト` のみ区切り自体が欠落している点は
明確な逸脱）。

---

## 軽微な指摘

### MINOR-1: `accuracy=None` に対する `# 必中` コメントの付与が一貫していない

**ファイル**: 例 `move_a.py:314`（あてみなげ）, `move_a.py:550`
（いじげんホール）, `move_ta.py:902`（でんげきは）, `move_ma.py:101`
（マジカルリーフ）vs `move_ka.py:507`（ガードシェア）, `move_ka.py:520`
（ガードスワップ）, `move_ta.py:991`（スキルスワップ, 942行目）

`accuracy=None`（`MoveData` のデフォルト値と同一だが明示している）を持つ
エントリのうち、変化技グループ（ガードシェア・ガードスワップ・パワーシェア・
パワースワップ・スピードスワップ・とおせんぼう・なみだめ等）はほぼ例外なく
`# 必中` コメントが付く一方、命中判定を持たないダメージ技グループ
（あてみなげ・いじげんホール・いじげんラッシュ・でんげきは・マジカルリーフ・
スピードスター等）は同じ `accuracy=None` でもコメントなしのことが多い。
実害はないが、「なぜ `accuracy=None` なのか」を読み手がその場で判断する
負担が技グループによって異なる。全件に统一的にコメントを付けるか、逆に
自明な場合は省略する方針をどちらかに決めて統一するとよい。

### MINOR-2: `handlers={}` の説明コメントは概ね統一されているが、文言のバリエーションがやや多い

**ファイル**: 例 `move_a.py:1154`「効果のないわざ（戦闘上の効果なし）」,
`move_ha.py:239`「効果のないわざ（戦闘上の効果なし）」,
`move_sa.py:165,196`「ダブル専用（本プロジェクトはシングルバトル専用のため
対象外）」, `move_ta.py:733,1511`「ダブル専用（本プロジェクトはシングル
バトル専用のため対象外）」, `move_a.py:600`「しれいとう連携のランクアップは
ダブル専用のため対象外（実装しない）」

「追加効果なし」（大多数、約100件）、「ダブル専用（...）」（同一文言で
複数回、一貫）、「効果のないわざ（...）」（同一文言で複数回、一貫）の3つの
定型句自体は使い回されており大きな問題はないが、`move_a.py:600` のみ
「ダブル専用」の定型句を使わず独自の文で説明している。内容は正しいが、
grep で「ダブル専用」を検索して未対応技を洗い出す際にこの1件が漏れる。
定型句への統一を推奨する（軽微）。

---

## 命名の一貫性・妥当性

### フィールド名（辞書キー）の統一性: 問題なし

`MoveData` の12フィールド（`type`, `category`, `pp`, `power`, `accuracy`,
`priority`, `critical_rank`, `target`, `flags`, `multi_hit`, `handlers`,
`lethal_handlers`）について、約850エントリ全件を確認した範囲で、キー名の
綴り違い・大文字小文字の不統一・別名の混入は一切見つからなかった。フィールドの
相対的な記述順序（存在するものだけを `type → category → pp → power →
accuracy → priority → critical_rank → target → flags → multi_hit →
handlers → lethal_handlers` の順で並べる）も全ファイルで一貫している。これは
`data/` 層の中でも特に統制が取れている部類だと言える。

### ハンドラ参照名（コールバック名）の命名パターン: 概ね統一、汎用ハンドラのみ分裂（ISSUE-3参照）

個別技専用ハンドラの命名は `<技名>_<効果内容>`
（例: `かみなり_apply_paralysis_to_defender`, `やきつくす_burn_item`）という
snake_case パターンで統一されており、`ON_DAMAGE_HIT` での追加効果付与、
`ON_CALC_POWER_MODIFIER` での威力計算、`ON_STATUS_HIT` での変化技効果、
といったイベント種別ごとに動詞のバリエーション
（`apply_*_to_defender`, `lower_defender_*`, `modify_defender_stats`,
`calc_power` 等）も技グループ間で一貫して再利用されている。一方、複数技が
共有する汎用ハンドラは英語/日本語+代表技名/日本語のみの3パターンに分裂して
おり（ISSUE-3）、特に `効果抜群時威力ブースト` はアンダースコア区切りの
慣習からも外れている。

### 技系統ごとの共通属性表現: `まもる`系は統一、`スワップ`系はハートスワップのみ逸脱（CRIT-2参照）

- **優先度技**: `priority` フィールドの単純な整数指定で統一。特殊優先度技
  （`priority=4` の「まもる」系、`priority=-6` の「ほえる」系等）で表記の
  ぶれはない。
- **連続技（`multi_hit`）**: キー名 `min`/`max`/`check_hit_each_time`/
  `power_sequence` は全エントリで統一。値の傾向も一貫（`check_hit_each_time`
  が `False` の場合は `power_sequence` を空タプル `()` にする、`True` の
  場合のみ実際の威力シーケンスを記述する）。書式（1行 vs 複数行）のみ
  `ふくろだたき` が例外（ISSUE-2）。
- **`まもる`系統（`ON_TRY_MOVE_2` + `hs.まもる系_連続使用失敗チェック`）**:
  まもる・かえんのまもり・キングシールド・こらえる・ニードルガード・
  ファストガード・トーチカ・スレッドトラップ・みきりの9技すべてが同一の
  共有ハンドラ `hs.まもる系_連続使用失敗チェック` を `Event.ON_TRY_MOVE_2` に
  登録しており、`priority` 省略（デフォルト100）も統一されている。
- **ランク入れ替え技統（`ガードスワップ`/`パワースワップ`/`スピードスワップ`/
  `ハートスワップ`）**: ハンドラ命名パターン（`<技名>_swap_ranks` /
  `<技名>_swap_speed`）は4技とも統一されているにもかかわらず、`accuracy`/
  `flags` の値だけ `ハートスワップ` が兄弟3技と異なる（CRIT-2）。「同じ
  ハンドラ命名規則に従っている技は、他の属性も揃っているはず」という前提が
  裏切られる実例であり、命名パターンの一貫性チェックが実データの不整合発見に
  直結した好例（かつ要修正事項）である。
- **二段技（`ON_MOVE_CHARGE` + `h.charge_into_volatile`）**: あなをほる・
  ダイビング・そらをとぶ・とびはねる（`そらをとぶ`と共有）・コールドフレア・
  ゴッドバード・フリーズボルト・ゴーストダイブ／シャドーダイブ（`move_ka.py`
  の「ゴーストダイブ」と`move_sa.py`の「シャドーダイブ」は共に volatile名
  `"シャドーダイブ"` を共有）の計8エントリすべてで `lambda b, c, v:
  h.charge_into_volatile(b, c, v, "<状態名>")` という同一パターンが使われて
  いる。`ゴーストダイブ`が`"シャドーダイブ"`という別名を参照している点は
  一見コピペミスに見えるが、`src/jpoke/data/volatile.py:315` に
  `VolatileData` として `"シャドーダイブ"` が定義されており、
  `src/jpoke/types/move.py:261` の `HIDDEN_MOVE_ALLOWED_MOVES`
  相当のリストにも両技名が併記されていることから、「ゴーストダイブ」は
  「シャドーダイブ」の技名変更後バージョンとして同一の内部揮発状態を共有する
  意図的な設計であることを確認した。**誤検出だが念のため確認する価値のある
  パターンだった**ため記録する。

### 五十音順ソートの遵守: 逸脱なし

`python scripts/sort_data/sort_moves.py --check` を実行し、11ファイルすべてで
`OK: 11 ファイルとも整列済み` の結果を得た。また同スクリプトを誤って
`--check` なしで実行してしまった際も差分が発生しなかった
（=空行除去等の副作用も含めて現状のファイルはスクリプトの正規形と一致して
いる）。目視でも五十音順違反は見つからなかった。

---

## 総評

`data/moves/` はフィールド名・記述順序・ソート順という「構造面」の一貫性は
非常に高く、スクリプトによる自動検証（`sort_moves.py --check`）も通過して
いる。今回の重点観点である「命名の一貫性」を軸に横断的に確認した結果、
構造面のノイズは少なかった一方で、**命名パターンが同一であることを手がかりに
実データの不整合を2件（CRIT-1, CRIT-2）発見**できた。特にCRIT-2
（`ハートスワップ`）は、「同じハンドラ命名規則`<技名>_swap_ranks`を持つ技は
`accuracy`/`flags`も同じ形であるべき」という命名一貫性の観点がなければ
見過ごされていた可能性が高く、単なるスタイルの指摘にとどまらない実質的な
発見だった。CRIT-1（`move_list.txt`参照切れ）は2026-07-11のドキュメント
リネームに`data/moves/`側のコメントが追随できていない「取り残された参照」で
あり、直近のドキュメント変更のたびに`data/moves/`内のコメントも横断
grepで確認する運用を推奨する。
