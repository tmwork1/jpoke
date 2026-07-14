"""Pokemon.render_info() / Pokemon.show() の出力文字列の回帰テスト。

以前は未所持アイテム・テラスタル未設定時の表示が英語ハードコード
（"No item" / "No terastal"）になっていたが、日本語表記
（"アイテムなし" / "テラスタルなし"）に変更した。この文字列が
意図せず英語に戻らないことを確認する。
"""
from jpoke import Pokemon


def test_render_info_アイテム所持時はアイテム名が表示される():
    """アイテムを所持している場合はアイテム名がそのまま表示される。"""
    mon = Pokemon("カビゴン", item_name="たべのこし")
    info = mon.render_info()
    assert "たべのこし" in info
    assert "アイテムなし" not in info


def test_render_info_アイテム未所持でアイテムなしと表示される():
    """アイテム未所持のポケモンは render_info() に「アイテムなし」を含む。"""
    mon = Pokemon("カビゴン")
    info = mon.render_info()
    assert "アイテムなし" in info
    assert "No item" not in info


def test_render_info_テラスタイプは基本タイプ由来で常に表示される():
    """tera_typeはPokemon.__init__でtera_type or self.base_types[0]により常に
    設定されるため、render_info()では「テラスタルなし」ではなく基本タイプ由来の
    テラスタイプ表記（例: 'ノーマルT'）が表示される。
    """
    mon = Pokemon("カビゴン")  # ノーマルタイプ、tera_type未指定
    info = mon.render_info()
    assert "ノーマルT" in info
    assert "テラスタルなし" not in info
    assert "No terastal" not in info


def test_show_render_infoと同じ内容をprintする(capsys):
    """show()はrender_info()の結果をprintするだけの薄いラッパー。"""
    mon = Pokemon("カビゴン")
    mon.show()
    captured = capsys.readouterr()
    assert captured.out.strip() == mon.render_info()
