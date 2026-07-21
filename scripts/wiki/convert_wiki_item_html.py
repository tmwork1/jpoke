#!/usr/bin/env python3
"""
.internal/wiki_html/items/*.html を読み込み、
テンプレート準拠のアイテム仕様書 .internal/spec/items/*.md を生成する。

- 対戦シミュレータに不要な要素（価格・ウッウロボ・こんな時に使おう）を除外
- 効果の種類が同じアイテムは GROUPS で定義したグループ仕様書にまとめる
"""

from pathlib import Path
import re
from bs4 import BeautifulSoup, NavigableString, Tag

PROJECT_DIR = Path(__file__).parent.parent.parent
HTML_DIR = PROJECT_DIR / "docs" / "wiki_html" / "items"
SPEC_DIR = PROJECT_DIR / "docs" / "spec" / "items"
TODAY = "2026-06-06"

# 出力する h2 セクション（この順で出力）
OUTPUT_SECTIONS = ["効果", "詳細な仕様", "備考", "関連項目"]

# セクション ID の別名を正規化するマップ
SECTION_ID_NORMALIZE = {
    "値段・効果": "効果",  # きのみページの別名
}

# スキップするセクション ID のキーワード（部分一致）
SKIP_H2_KEYWORDS = [
    "説明文",
    "入手方法",
    "交換",
    "こんな",   # こんなときに使おう / こんな時に使おう
    "各言語版",
    "アニメ",
    "不思議のダンジョン",
    "ポケモンカード",
    "カードゲーム",
    "Trading_Card_Game",
    "Pocket",
    "スリープ",
    "マスターズ",
    "味",       # きのみの味セクション
]

# 効果セクション内でスキップする箇条書きの先頭キーワード（先頭一致）
SKIP_EFFECT_LINE_STARTS = [
    # 全アイテム共通
    "買値", "売値", "ウッウロボ",
    # きのみ固有（バトル非関連のゲームコンテンツ）
    "きのみクラッシュ",
    "アイスクリーム",
    "しるや",
    "カロス地方",
    "突然変異",
    "そめものや",
    "カレーライス",
]

# 効果セクション内のネスト行でスキップするコンテンツパターン（部分一致）
SKIP_EFFECT_NESTED_PATTERNS = [
    "のみ×",  # 染め物・突然変異レシピ（例: オボンのみ×15+...→パステルイエロー）
]

# 備考セクション内でスキップする行（部分一致）
SKIP_BIKO_KEYWORDS = [
    "スマッシュブラザーズ",    # スマブラ
    "SPECIAL",                 # ポケモンSPECIAL漫画
    "ポケモンスタジアム",
    "ニンテンドーカップ",
    "ニンテンドウカップ",      # 表記ゆれ
    "カンポーやく",            # 薬材（バトル非関連）
    "アニメでは",
    "アニメで",
    "アニメにおいて",
    "NPC",                     # ゲーム内NPCのセリフ・所持情報
    "げんきでちゅう",          # ピカチュウスピンオフゲーム
    "はねろ",                  # Magikarp Jump（モバイル）
    "バトルバイキング",        # アローラのレストラン（ゲーム外コンテンツ）
    "コロシアム",              # GameCubeスピンオフ
    "しるや",                  # きのみジュース屋
    "コンポスタ",              # きのみ農場（旧世代コンテンツ）
    "ジョインアベニュー",      # 旧世代通信施設
    "ポケリゾート",            # 旧世代コンテンツ
    "バトルレボリューション",  # Wiiスピンオフ
    "ポケモン☆サンデー",      # バラエティ番組
    "劇場版",                  # 映画参照
    "フレンドリィショップ",    # 旧世代ショップ入手情報
    "マスターズ",              # ポケモンマスターズ（モバイル）
    "ポケリゾート",
    "グラフィック上",          # グラフィックの見た目に関するトリビア
    "説明文",                  # 旧世代の説明文に関するトリビア
    "ベータ版",                # 旧作のベータ版情報
    "コニコシティ",            # 旧世代の街（食事処）
    "同音異字",                # 命名トリビア
    "韓国語版",                # 多言語版注記
    "中国語版",                # 多言語版注記
]

# 備考セクション内でスキップする行（正規表現、content に対して適用）
_OLD_GAME_TITLES = (
    "ルビー|サファイア|エメラルド|金・銀|ハートゴールド|ソウルシルバー"
    "|ブラック|ホワイト|X・Y|オメガルビー|アルファサファイア"
    "|サン・ムーン|ウルトラサン|ウルトラムーン|ソード・シールド"
    "|BDSP|ポケモンXD|Pokémon LEGENDS"
)
SKIP_BIKO_RE = [
    r"と思われ",              # 語源・由来（モデルは〇〇と思われる）
    r"由来は",                # 語源
    r"とは.{0,15}のこと",     # "〇〇とは〇〇のこと" 語源・語釈
    # 旧世代ゲームタイトルを主語にした入手・挙動情報（content = "- " 除去後）
    rf"^({_OLD_GAME_TITLES})",
]

# 関連項目セクション内でスキップする行（部分一致）
SKIP_KANREN_KEYWORDS = [
    "カードゲーム",
    "（ダンジョン）",
    "(ダンジョン)",
]

# 全セクション共通: 旧世代情報を行内から除去するパターン（正規表現）
STRIP_OLD_GEN_RE = [
    # (第X世代では.../第X世代まで.../第X世代のみ...) 形式の括弧注釈を除去
    r"\([^)]*第[一二三四五六七八]世代(?:では|まで|のみ)[^)]*\)",
    # (LEGENDS アルセウスでは...) 形式の括弧注釈を除去
    r"\(LEGENDS\s+アルセウスでは[^)]*\)",
    # LEGENDS アルセウス固有のゲームプレイ記述（野生投げ）を除去
    r"LEGENDS\s+アルセウスでは野生ポケモンの近くに投げて[^。]*。\s*",
]

# グループ仕様書の定義: ファイル名 → アイテム名リスト（このリスト順で出力）
GROUPS: dict[str, list[str]] = {
    "こだわり系": [
        "こだわりスカーフ",
        "こだわりハチマキ",
        "こだわりメガネ",
    ],
    "天候石": [
        "あついいわ",
        "しめったいわ",
        "さらさらいわ",
        "つめたいいわ",
    ],
    "フィールドシード": [
        "グラスシード",
        "エレキシード",
        "ミストシード",
        "サイコシード",
    ],
    "タイプ半減きのみ": [
        # 効果バツグンのタイプわざのダメージを 1/2 にする（タイプ別）
        "ヤチェのみ",   # こおり
        "タンガのみ",   # むし
        "バコウのみ",   # ひこう
        "ソクノのみ",   # でんき
        "イトケのみ",   # みず
        "リンドのみ",   # くさ
        "オッカのみ",   # ほのお
        "シュカのみ",   # じめん
        "ウタンのみ",   # エスパー
        "ビアーのみ",   # どく
        "カシブのみ",   # ゴースト
        "ホズのみ",    # ノーマル
        "ナモのみ",    # あく
        "ハバンのみ",   # ドラゴン
        "ヨプのみ",    # かくとう
        "ヨロギのみ",   # いわ
        "リリバのみ",   # はがね
        "ロゼルのみ",   # フェアリー
    ],
    "HP回復ピンチきのみ": [
        # HP が低下したときに自動回復
        "オレンのみ",   # 10固定回復・HP1/2 以下でトリガー・こんらんなし
        "オボンのみ",   # 1/4 回復・HP1/2 以下でトリガー・こんらんなし
        "フィラのみ",   # 1/3 回復・HP1/4 以下でトリガー・からい→こんらん
        "ウイのみ",    # 1/3 回復・HP1/4 以下でトリガー・しぶい→こんらん
        "マゴのみ",    # 1/3 回復・HP1/4 以下でトリガー・あまい→こんらん
        "バンジのみ",   # 1/3 回復・HP1/4 以下でトリガー・にがい→こんらん
        "イアのみ",    # 1/3 回復・HP1/4 以下でトリガー・すっぱい→こんらん
    ],
    "ランク上昇ピンチきのみ": [
        # HP が低下したとき、または被弾時にランクや状態が変化する
        "チイラのみ",   # こうげき +1（HP1/4 以下）
        "ヤタピのみ",   # とくこう +1（HP1/4 以下）
        "リュガのみ",   # ぼうぎょ +1（HP1/4 以下）
        "ズアのみ",    # とくぼう +1（HP1/4 以下）
        "カムラのみ",   # すばやさ +1（HP1/4 以下）
        "アッキのみ",   # ぼうぎょ +1（物理被弾直後）
        "タラプのみ",   # とくぼう +1（特殊被弾直後）
        "スターのみ",   # ランダム +2（HP1/4 以下）
        "イバンのみ",   # 先制発動（HP1/4 以下）
        "サンのみ",    # きゅうしょ状態（HP1/4 以下）
        "ミクルのみ",   # 命中率 1.2 倍（HP1/4 以下）
    ],
    "状態回復きのみ": [
        # 特定または全状態異常を回復する
        "カゴのみ",    # ねむり
        "クラボのみ",   # まひ
        "チーゴのみ",   # やけど
        "ナナシのみ",   # こおり
        "モモンのみ",   # どく・もうどく
        "キーのみ",    # こんらん
        "ラムのみ",    # 全状態異常
    ],
    "タイプ強化アイテム": [
        # 対応タイプのわざ威力を 1.2 倍にする（18 タイプ分）
        "シルクのスカーフ",  # ノーマル
        "もくたん",        # ほのお
        "しんぴのしずく",   # みず
        "じしゃく",        # でんき
        "きせきのタネ",     # くさ
        "とけないこおり",   # こおり
        "くろおび",        # かくとう
        "どくバリ",        # どく
        "やわらかいすな",   # じめん
        "するどいくちばし", # ひこう
        "まがったスプーン", # エスパー
        "ぎんのこな",      # むし
        "かたいいし",      # いわ
        "のろいのおふだ",   # ゴースト
        "りゅうのキバ",    # ドラゴン
        "くろいメガネ",    # あく
        "メタルコート",    # はがね
        "ようせいのハネ",  # フェアリー
    ],
    "おめん": [
        # オーガポン専用仮面。フォルム・タイプ・テラスタイプを変え、攻撃技威力を 1.2 倍にする
        "いどのめん",     # みずタイプ
        "かまどのめん",   # ほのおタイプ
        "いしずえのめん", # いわタイプ
    ],
}

# グループに属するアイテム名の逆引きセット
_GROUPED_ITEMS: set[str] = {item for items in GROUPS.values() for item in items}

# グループ仕様書の先頭に出力する比較テーブルの定義
GROUP_TABLES: dict[str, dict] = {
    "こだわり系": {
        "columns": ["アイテム", "強化ステータス", "なげつける"],
        "rows": [
            ["こだわりスカーフ", "すばやさ×1.5", "威力10"],
            ["こだわりハチマキ", "こうげき×1.5", "威力10"],
            ["こだわりメガネ",   "とくこう×1.5",  "威力10"],
        ],
        "note": "共通: 最初に選択したわざしか使用できなくなる。",
    },
    "天候石": {
        "columns": ["アイテム", "発動天候", "なげつける"],
        "rows": [
            ["あついいわ",   "にほんばれ（5ターン）",  "威力30"],
            ["しめったいわ", "あめ（5ターン）",        "威力30"],
            ["さらさらいわ", "すなあらし（5ターン）",  "威力30"],
            ["つめたいいわ", "ゆき（5ターン）",        "威力30"],
        ],
        "note": "共通: 投げた瞬間に天候を変化させる（道具の効果）。",
    },
    "フィールドシード": {
        "columns": ["アイテム", "対応地形", "効果", "なげつける"],
        "rows": [
            ["グラスシード", "グラスフィールド",  "ぼうぎょ+1",  "威力10"],
            ["エレキシード", "エレキフィールド",  "ぼうぎょ+1",  "威力10"],
            ["ミストシード", "ミストフィールド",  "とくぼう+1",  "威力10"],
            ["サイコシード", "サイコフィールド",  "とくぼう+1",  "威力10"],
        ],
        "note": "共通: 対応するフィールドが展開されているとき、場に出た瞬間に消費してランク上昇。",
    },
    "タイプ半減きのみ": {
        "columns": ["きのみ", "半減タイプ", "なげつける"],
        "rows": [
            ["ヤチェのみ", "こおり",    "威力10"],
            ["タンガのみ", "むし",      "威力10"],
            ["バコウのみ", "ひこう",    "威力10"],
            ["ソクノのみ", "でんき",    "威力10"],
            ["イトケのみ", "みず",      "威力10"],
            ["リンドのみ", "くさ",      "威力10"],
            ["オッカのみ", "ほのお",    "威力10"],
            ["シュカのみ", "じめん",    "威力10"],
            ["ウタンのみ", "エスパー",  "威力10"],
            ["ビアーのみ", "どく",      "威力10"],
            ["カシブのみ", "ゴースト",  "威力10"],
            ["ホズのみ",   "ノーマル",  "威力10"],
            ["ナモのみ",   "あく",      "威力10"],
            ["ハバンのみ", "ドラゴン",  "威力10"],
            ["ヨプのみ",   "かくとう",  "威力10"],
            ["ヨロギのみ", "いわ",      "威力10"],
            ["リリバのみ", "はがね",    "威力10"],
            ["ロゼルのみ", "フェアリー","威力10"],
        ],
        "note": "共通: 対応タイプの効果バツグンのわざを受けたとき、ダメージを1/2にして消費。",
    },
    "HP回復ピンチきのみ": {
        "columns": ["きのみ", "発動条件", "回復量", "こんらん"],
        "rows": [
            ["オレンのみ", "HP1/2以下", "10固定",      "なし"],
            ["オボンのみ", "HP1/2以下", "最大HPの1/4", "なし"],
            ["フィラのみ", "HP1/4以下", "最大HPの1/3", "からい嫌いのせいかく"],
            ["ウイのみ",   "HP1/4以下", "最大HPの1/3", "しぶい嫌いのせいかく"],
            ["マゴのみ",   "HP1/4以下", "最大HPの1/3", "あまい嫌いのせいかく"],
            ["バンジのみ", "HP1/4以下", "最大HPの1/3", "にがい嫌いのせいかく"],
            ["イアのみ",   "HP1/4以下", "最大HPの1/3", "すっぱい嫌いのせいかく"],
        ],
        "note": "共通: 発動条件を満たした瞬間に自動消費してHP回復。じゅくせい持ちは回復量2倍。",
    },
    "ランク上昇ピンチきのみ": {
        "columns": ["きのみ", "変化内容", "発動条件"],
        "rows": [
            ["チイラのみ", "こうげき+1",    "HP1/4以下"],
            ["ヤタピのみ", "とくこう+1",    "HP1/4以下"],
            ["リュガのみ", "ぼうぎょ+1",    "HP1/4以下"],
            ["ズアのみ",   "とくぼう+1",    "HP1/4以下"],
            ["カムラのみ", "すばやさ+1",    "HP1/4以下"],
            ["アッキのみ", "ぼうぎょ+1",    "物理被弾直後"],
            ["タラプのみ", "とくぼう+1",    "特殊被弾直後"],
            ["スターのみ", "ランダム+2",    "HP1/4以下"],
            ["イバンのみ", "そのターン先制", "HP1/4以下"],
            ["サンのみ",   "きゅうしょ状態", "HP1/4以下"],
            ["ミクルのみ", "命中率×1.2",    "HP1/4以下"],
        ],
        "note": "共通: じゅくせい持ちはアッキ・タラプを除き効果量2倍。",
    },
    "状態回復きのみ": {
        "columns": ["きのみ", "回復する状態異常", "なげつける"],
        "rows": [
            ["カゴのみ",   "ねむり",      "威力10"],
            ["クラボのみ", "まひ",        "威力10"],
            ["チーゴのみ", "やけど",      "威力10"],
            ["ナナシのみ", "こおり",      "威力10"],
            ["モモンのみ", "どく・もうどく","威力10"],
            ["キーのみ",   "こんらん",    "威力10"],
            ["ラムのみ",   "全状態異常",  "威力10"],
        ],
        "note": "共通: 対応する状態異常になった瞬間に自動消費して回復。ラムのみはねむり以外の揮発性状態は回復しない。",
    },
    "タイプ強化アイテム": {
        "columns": ["アイテム", "強化タイプ", "なげつける"],
        "rows": [
            ["シルクのスカーフ",  "ノーマル",   "威力10"],
            ["もくたん",         "ほのお",     "威力30"],
            ["しんぴのしずく",   "みず",       "威力30"],
            ["じしゃく",         "でんき",     "威力30"],
            ["きせきのタネ",     "くさ",       "威力30"],
            ["とけないこおり",   "こおり",     "威力30"],
            ["くろおび",         "かくとう",   "威力30"],
            ["どくバリ",         "どく",       "威力30"],
            ["やわらかいすな",   "じめん",     "威力30"],
            ["するどいくちばし", "ひこう",     "威力30"],
            ["まがったスプーン", "エスパー",   "威力30"],
            ["ぎんのこな",       "むし",       "威力30"],
            ["かたいいし",       "いわ",       "威力30"],
            ["のろいのおふだ",   "ゴースト",   "威力30"],
            ["りゅうのキバ",     "ドラゴン",   "威力30"],
            ["くろいメガネ",     "あく",       "威力30"],
            ["メタルコート",     "はがね",     "威力30"],
            ["ようせいのハネ",   "フェアリー", "威力10"],
        ],
        "note": "共通: 対応タイプのわざの威力を1.2倍にする。",
    },
    "おめん": {
        "columns": ["アイテム", "フォーム", "テラスタイプ", "なげつける"],
        "rows": [
            ["いどのめん",    "いどのめんオーガポン",    "みず", "オーガポンは失敗/他は威力60"],
            ["かまどのめん",  "かまどのめんオーガポン",  "ほのお","オーガポンは失敗/他は威力60"],
            ["いしずえのめん","いしずえのめんオーガポン","いわ",  "オーガポンは失敗/他は威力60"],
        ],
        "note": "共通: オーガポン専用。フォルムとタイプを変え、全攻撃技の威力を1.2倍にする。テラスタル時はテラスタイプ一致ボーナスが1.5倍→2倍になる。",
    },
}


def _should_skip_section(section_id: str) -> bool:
    return any(kw in section_id for kw in SKIP_H2_KEYWORDS)


def is_old_gen_only_h3(text: str) -> bool:
    """第9世代より前の特定世代のみに適用する h3 なら True を返す（スキップ対象）。"""
    if "世代" not in text:
        return False
    if "第九世代" in text:
        return False
    if re.search(r"第[一二三四五六七八]世代以降", text):
        return False
    return True


def elem_to_md(node, depth: int = 0) -> str:
    """BS4 ノードを再帰的に Markdown テキストへ変換する。"""
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return str(node)

    tag = node.name
    if not tag or tag in ("script", "style", "meta"):
        return ""

    if tag == "a":
        return node.get_text()

    if tag in ("b", "strong", "i", "em", "sup", "sub"):
        return "".join(elem_to_md(c, depth) for c in node.children)

    if tag == "span":
        if node.get("id", "").startswith("."):
            return ""
        return "".join(elem_to_md(c, depth) for c in node.children)

    if tag == "p":
        inner = "".join(elem_to_md(c, depth) for c in node.children).strip()
        return inner + "\n" if inner else ""

    if tag == "ul":
        parts = [_li_to_md(li, depth) for li in node.find_all("li", recursive=False)]
        return "\n".join(parts) + "\n" if parts else ""

    if tag == "ol":
        parts = [
            _li_to_md(li, depth, ordered=True, num=i)
            for i, li in enumerate(node.find_all("li", recursive=False), 1)
        ]
        return "\n".join(parts) + "\n" if parts else ""

    if tag == "dl":
        return _dl_to_md(node)

    if tag == "table":
        return _table_to_md(node)

    if tag in ("h3", "h4"):
        level = "#" * int(tag[1])
        headline = node.find("span", class_="mw-headline")
        text = headline.get_text().strip() if headline else node.get_text().strip()
        return f"\n{level} {text}\n"

    if tag == "br":
        return "\n"

    return "".join(elem_to_md(c, depth) for c in node.children)


def _li_to_md(li: Tag, depth: int = 0, ordered: bool = False, num: int = 1) -> str:
    indent = "  " * depth
    prefix = f"{num}. " if ordered else "- "

    text_parts: list[str] = []
    nested_blocks: list[str] = []

    for child in li.children:
        if isinstance(child, NavigableString):
            text_parts.append(str(child))
        elif child.name in ("ul", "ol"):
            nested_blocks.append(elem_to_md(child, depth + 1))
        else:
            text_parts.append(elem_to_md(child, depth))

    text = "".join(text_parts).strip()
    result = indent + prefix + text
    if nested_blocks:
        result += "\n" + "".join(nested_blocks).rstrip()
    return result


def _dl_to_md(dl: Tag) -> str:
    parts: list[str] = []
    current_dt = ""
    for child in dl.children:
        if isinstance(child, NavigableString):
            continue
        if child.name == "dt":
            current_dt = child.get_text().strip()
        elif child.name == "dd":
            dd_content = "".join(elem_to_md(c) for c in child.children).strip()
            if not dd_content:
                continue
            if current_dt:
                parts.append(f"- {current_dt}: {dd_content}")
                current_dt = ""
            else:
                parts.append(dd_content)
    return "\n".join(parts) + "\n" if parts else ""


def _table_to_md(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            text = cell.get_text().strip().replace("\n", " ").replace("|", "｜")
            cells.append(text)
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    max_cols = max(len(r) for r in rows)
    padded = [r + [""] * (max_cols - len(r)) for r in rows]

    lines: list[str] = []
    for i, row in enumerate(padded):
        lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    return "\n".join(lines) + "\n"


def _get_section_elements(h2_node: Tag) -> list[Tag]:
    """h2 から次の h2 までの要素を収集し、旧世代限定 h3/h4 と boilerplate をスキップする。"""
    elements: list[Tag] = []
    skip_mode = False

    node = h2_node.next_sibling
    while node is not None:
        if isinstance(node, NavigableString):
            node = node.next_sibling
            continue

        if node.name == "h2":
            break

        if node.name in ("h3", "h4"):
            headline = node.find("span", class_="mw-headline")
            h_text = headline.get_text().strip() if headline else node.get_text().strip()
            if is_old_gen_only_h3(h_text):
                skip_mode = True
            else:
                skip_mode = False
                elements.append(node)
        elif not skip_mode:
            if isinstance(node, Tag) and "boilerplate" in node.get("class", []):
                pass
            else:
                elements.append(node)

        node = node.next_sibling

    return elements


def _ref_url(soup: BeautifulSoup) -> str:
    canonical = soup.find("link", {"rel": "canonical"})
    if canonical:
        href = canonical.get("href", "")
        m = re.search(r"/wiki/(.+)$", href)
        if m:
            return f"https://wiki.xn--rckteqa2e.com/wiki/{m.group(1)}"
    return ""


def _elems_to_md_no_tables(elements: list[Tag]) -> str:
    parts: list[str] = []
    for elem in elements:
        if isinstance(elem, Tag) and elem.name == "table":
            continue
        content = elem_to_md(elem).strip()
        if content:
            parts.append(content)
    return "\n".join(parts)


def _filter_effect_md(md: str) -> str:
    """効果セクションの Markdown から対戦非関連行を除去する。"""
    result = []
    for line in md.split("\n"):
        content = line.strip().removeprefix("- ").strip()
        # 先頭キーワードマッチ（全深さ対象）
        if any(content.startswith(kw) for kw in SKIP_EFFECT_LINE_STARTS):
            continue
        # ネスト行（インデントあり）のコンテンツパターンマッチ
        if line.startswith("  ") and any(kw in content for kw in SKIP_EFFECT_NESTED_PATTERNS):
            continue
        # 実質空のリスト行（インライン除去後に残る "  -" など）をスキップ
        if re.match(r"^\s*-\s*$", line):
            continue
        result.append(line)
    return "\n".join(result).strip()


def _filter_biko_md(md: str) -> str:
    """備考セクションから対戦非関連行を除去する。親行が除去された場合、子行も除去する。"""
    result = []
    parent_removed = False  # 直前のトップレベル行が除去されたか
    for line in md.split("\n"):
        is_child = line.startswith("  ")  # インデントあり = 子行
        content = line.strip().removeprefix("- ").strip()
        should_skip = (
            any(kw in content for kw in SKIP_BIKO_KEYWORDS)
            or any(re.search(pat, content) for pat in SKIP_BIKO_RE)
        )
        # 子行: 親が除去されていれば無条件でスキップ
        if is_child and parent_removed:
            should_skip = True
        if should_skip:
            if not is_child:
                parent_removed = True
            continue
        if line.strip():  # 実内容がある行でフラグをリセット
            if not is_child:
                parent_removed = False
        result.append(line)
    return "\n".join(result).strip()


def _filter_kanren_md(md: str) -> str:
    """関連項目セクションから対戦非関連リンクを除去する。"""
    result = []
    for line in md.split("\n"):
        if any(kw in line for kw in SKIP_KANREN_KEYWORDS):
            continue
        result.append(line)
    return "\n".join(result).strip()


def _strip_old_gen_text(md: str) -> str:
    """Markdown テキストから旧世代限定の注釈をインライン除去する。"""
    for pattern in STRIP_OLD_GEN_RE:
        md = re.sub(pattern, "", md)
    # 除去後に生じる連続スペースを整理
    md = re.sub(r"  +", " ", md)
    # 除去後に実質空になったリスト行を除去
    md = "\n".join(
        line for line in md.split("\n")
        if not re.match(r"^\s*-\s*$", line)
    )
    return md


def _indent_headers(md: str, times: int = 1) -> str:
    """Markdown の全見出しを times レベル深くする (## → ### など)。"""
    prefix = "#" * times
    return "\n".join(
        prefix + line if line.startswith("#") else line
        for line in md.split("\n")
    )


def process_html(html_path: Path) -> dict:
    """HTML ファイルを解析して各セクション内容を返す。"""
    item_name = html_path.stem
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    ref_url = _ref_url(soup)

    parser_output = soup.find("div", class_="mw-parser-output")
    if not parser_output:
        return {"name": item_name, "ref_url": ref_url, "contents": {}}

    raw_sections: dict[str, list[Tag]] = {}
    for h2 in parser_output.find_all("h2"):
        headline = h2.find("span", class_="mw-headline")
        if not headline:
            continue
        section_id = headline.get("id", "")
        if _should_skip_section(section_id):
            continue
        normalized_id = SECTION_ID_NORMALIZE.get(section_id, section_id)
        if normalized_id in OUTPUT_SECTIONS:
            raw_sections[normalized_id] = _get_section_elements(h2)

    contents: dict[str, str] = {}
    for section_name in OUTPUT_SECTIONS:
        elems = raw_sections.get(section_name, [])
        if elems:
            if section_name == "関連項目":
                md = _elems_to_md_no_tables(elems)
            else:
                md = "".join(elem_to_md(e) for e in elems).strip()
            if section_name == "効果":
                md = _filter_effect_md(md)
            elif section_name == "備考":
                md = _filter_biko_md(md)
            elif section_name == "関連項目":
                md = _filter_kanren_md(md)
            md = _strip_old_gen_text(md)
            contents[section_name] = md
        else:
            contents[section_name] = ""

    return {"name": item_name, "ref_url": ref_url, "contents": contents}


def _render_item_sections(contents: dict[str, str], h_level: int) -> str:
    """セクション内容を Markdown に変換する。h_level=2 が単独、h_level=3 がグループ内。"""
    prefix = "#" * h_level
    out: list[str] = []
    for section_name in OUTPUT_SECTIONS:
        out.append(f"{prefix} {section_name}")
        content = contents.get(section_name, "").strip()
        if content:
            if h_level > 2:
                content = _indent_headers(content, times=h_level - 2)
            out.append(content)
            out.append("")
        else:
            if section_name == "備考":
                out.append("<!-- 内部処理の補足など。なければ省略可 -->")
            elif section_name == "関連項目":
                out.append("<!-- 関連する技・特性・アイテムなど。なければ省略可 -->")
            out.append("")
    return "\n".join(out)


def render_single(data: dict) -> str:
    """単独アイテムの仕様書を生成する。"""
    out = [
        f"# 仕様書: {data['name']}",
        "",
        f"調査日: {TODAY}",
        f"参照URL: {data['ref_url']}",
        "",
        _render_item_sections(data["contents"], h_level=2),
    ]
    return "\n".join(out)


def _render_group_header(group_name: str, items_data: list[dict]) -> list[str]:
    """収録アイテム一覧と比較テーブルを出力する。"""
    out: list[str] = ["## 収録アイテム", ""]

    table_def = GROUP_TABLES.get(group_name)
    if table_def:
        cols = table_def["columns"]
        rows = table_def["rows"]
        out.append("| " + " | ".join(cols) + " |")
        out.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for row in rows:
            out.append("| " + " | ".join(row) + " |")
        if note := table_def.get("note"):
            out.append("")
            out.append(f"- {note}")
    else:
        # テーブル定義がない場合はリストのみ
        for data in items_data:
            out.append(f"- {data['name']}")

    out.append("")
    out.append("---")
    out.append("")
    return out


def render_group(group_name: str, items_data: list[dict]) -> str:
    """グループ仕様書を生成する。"""
    out = [
        f"# 仕様書: {group_name}",
        "",
        f"調査日: {TODAY}",
        "",
    ]
    out.extend(_render_group_header(group_name, items_data))
    for i, data in enumerate(items_data):
        if i > 0:
            out.append("---")
            out.append("")
        out.append(f"## {data['name']}")
        out.append("")
        out.append(f"参照URL: {data['ref_url']}")
        out.append("")
        out.append(_render_item_sections(data["contents"], h_level=3))
    return "\n".join(out)


def main() -> None:
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    html_files = {p.stem: p for p in sorted(HTML_DIR.glob("*.html"))}
    print(f"{len(html_files)} 件のHTMLファイルを処理します。")

    item_data: dict[str, dict] = {}
    for name, path in html_files.items():
        try:
            item_data[name] = process_html(path)
        except Exception as e:
            print(f"  PARSE NG {name}: {e}")

    ok = ng = 0

    for group_name, item_names in GROUPS.items():
        spec_path = SPEC_DIR / f"_{group_name}.md"
        try:
            missing = [n for n in item_names if n not in item_data]
            if missing:
                print(f"  WARN {group_name}: HTML なし {missing}")
            items = [item_data[n] for n in item_names if n in item_data]
            if not items:
                print(f"  SKIP {group_name}: 対象アイテムが0件")
                continue
            md = render_group(group_name, items)
            spec_path.write_text(md, encoding="utf-8")
            print(f"  OK _{group_name}.md ({len(items)} items)")
            ok += 1
        except Exception as e:
            print(f"  NG {group_name}: {e}")
            ng += 1

    for name, data in item_data.items():
        if name in _GROUPED_ITEMS:
            continue
        spec_path = SPEC_DIR / f"{name}.md"
        try:
            md = render_single(data)
            spec_path.write_text(md, encoding="utf-8")
            print(f"  OK {name}")
            ok += 1
        except Exception as e:
            print(f"  NG {name}: {e}")
            ng += 1

    # グループ済みアイテムの個別ファイルと、_ なしの旧グループファイルを削除
    deleted = 0
    for name in _GROUPED_ITEMS:
        p = SPEC_DIR / f"{name}.md"
        if p.exists():
            p.unlink()
            print(f"  DEL {name}.md (グループ済み)")
            deleted += 1
    for group_name in GROUPS:
        old_path = SPEC_DIR / f"{group_name}.md"
        if old_path.exists():
            old_path.unlink()
            print(f"  DEL {group_name}.md (旧グループファイル)")
            deleted += 1

    print(f"\n完了: 生成 {ok} 件、削除 {deleted} 件、失敗 {ng} 件")


if __name__ == "__main__":
    main()
