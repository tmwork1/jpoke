import jaconv
import unicodedata
from rapidfuzz.distance import Levenshtein


def find_most_similar(str_list: list[str], s: str, ignore_dakuten: bool = False) -> str:
    """最も似ている要素を返す"""
    if s in str_list:
        return s

    s1 = jaconv.hira2kata(s)
    if ignore_dakuten:
        s1 = remove_dakuten(s1)
        str_list = list(map(remove_dakuten, str_list))

    distances = [Levenshtein.distance(s1, jaconv.hira2kata(item)) for item in str_list]

    return str_list[distances.index(min(distances))]


def japanese_char_ratio(s: str) -> float:
    """日本語の文字の割合を計算

    Args:
        s: 対象文字列

    Returns:
        日本語文字の割合 (0.0-1.0)
    """
    if not s:
        return 0.0

    jp_count = 0
    for c in s:
        try:
            name = unicodedata.name(c)
            if any(keyword in name for keyword in ["HIRAGANA", "KATAKANA", "CJK UNIFIED"]):
                jp_count += 1
        except ValueError:
            # 名前のない文字は無視
            pass

    return jp_count / len(s)


def to_upper_japanese(s) -> str:
    """小文字から大文字に変換"""
    trans = str.maketrans('ぁぃぅぇぉっゃゅょァィゥェォッャュョ', 'あいうえおつやゆよアイウエオツヤユヨ')
    return s.translate(trans)


def remove_dakuten(s) -> str:
    """濁点を除去"""
    trans = str.maketrans(
        'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ',
        'かきくけこさしすせそたちつてとはひふへほはひふへほカキクケコサシスセソタチツテトハヒフヘホハヒフヘホ'
    )
    return s.translate(trans)
