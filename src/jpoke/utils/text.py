import unicodedata


def jpn_char_ratio(s):
    """日本語の文字の割合"""
    if not s:
        return 0
    bools = [any(name in unicodedata.name(c) for name in
                 ["HIRAGANA", "KATAKANA", "CJK UNIFIED"]) for c in s]
    return sum(bools)/len(bools)


def to_upper_jpn(s):
    """小文字から大文字に変換"""
    trans = str.maketrans('ぁぃぅぇぉっゃゅょァィゥェォッャュョ', 'あいうえおつやゆよアイウエオツヤユヨ')
    return s.translate(trans)


def remove_dakuten(s):
    """濁点を除去"""
    trans = str.maketrans(
        'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ',
        'かきくけこさしすせそたちつてとはひふへほはひふへほカキクケコサシスセソタチツテトハヒフヘホハヒフヘホ'
    )
    return s.translate(trans)
