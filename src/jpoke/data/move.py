from jpoke.core.event import Event, Handler
from .models import MoveData
from jpoke.handlers import common, move as hdl


MOVES: dict[str, MoveData] = {
    "１０まんばりき": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 95,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "３ぼんのや": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "ＤＤラリアット": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "Ｇのちから": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "B": -1
            }
        ]
    },
    "アームハンマー": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,
        flags=["contact", "punch"],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.modify_stat(b, c, "self", "S", -1))}
    ),
    "アイアンテール": {
        "type": "はがね",
        "category": "物理",
        "pp": 15,
        "power": 100,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "B": -1
            }
        ]
    },
    "アイアンヘッド": {
        "type": "はがね",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "アイアンローラー": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 130,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "アイススピナー": {
        "type": "こおり",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "アイスハンマー": {
        "type": "こおり",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "アクアカッター": {
        "type": "みず",
        "category": "物理",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "slash",
            "high_critical"
        ]
    },
    "アクアジェット": {
        "type": "みず",
        "category": "物理",
        "pp": 20,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "アクアステップ": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "アクアテール": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "アクアブレイク": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "B": -1
            }
        ]
    },
    "アクセルブレイク": {
        "type": "かくとう",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "アクセルロック": {
        "type": "いわ",
        "category": "物理",
        "pp": 20,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "アクロバット": {
        "type": "ひこう",
        "category": "物理",
        "pp": 15,
        "power": 55,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "あなをほる": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "hide"
        ]
    },
    "あばれる": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "rage"
        ]
    },
    "あんこくきょうだ": {
        "type": "あく",
        "category": "物理",
        "pp": 5,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "critical",
            "punch"
        ]
    },
    "イカサマ": {
        "type": "あく",
        "category": "物理",
        "pp": 15,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "いかりのまえば": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 0,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "いじげんラッシュ": {
        "type": "あく",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "anti_protect"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1
            }
        ]
    },
    "いっちょうあがり": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "いわおとし": {
        "type": "いわ",
        "category": "物理",
        "pp": 15,
        "power": 50,
        "accuracy": 90,
        "priority": 0
    },
    "いわくだき": {
        "type": "かくとう",
        "category": "物理",
        "pp": 15,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "B": -1
            }
        ]
    },
    "いわなだれ": {
        "type": "いわ",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "インファイト": {
        "type": "かくとう",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1,
                "D": -1
            }
        ]
    },
    "ウェーブタックル": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "うちおとす": {
        "type": "いわ",
        "category": "物理",
        "pp": 15,
        "power": 50,
        "accuracy": 100,
        "priority": 0
    },
    "ウッドハンマー": {
        "type": "くさ",
        "category": "物理",
        "pp": 15,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "ウッドホーン": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "うっぷんばらし": {
        "type": "あく",
        "category": "物理",
        "pp": 5,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "えだづき": {
        "type": "くさ",
        "category": "物理",
        "pp": 40,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "オーラぐるま": {
        "type": "でんき",
        "category": "物理",
        "pp": 10,
        "power": 110,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "おどろかす": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 15,
        "power": 30,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "おはかまいり": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0
    },
    "かいりき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "カウンター": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": -5,
        "flags": [
            "contact"
        ]
    },
    "かえんぐるま": {
        "type": "ほのお",
        "category": "物理",
        "pp": 25,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "かえんボール": {
        "type": "ほのお",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "bullet",
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "かかとおとし": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_miss",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "かげうち": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "かげぬい": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "かたきうち": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "かみくだく": {
        "type": "あく",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bite",
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "B": -1
            }
        ]
    },
    "かみつく": {
        "type": "あく",
        "category": "物理",
        "pp": 25,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bite",
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "かみなりのキバ": {
        "type": "でんき",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "flinch": 1
            }
        ]
    },
    "かみなりパンチ": {
        "type": "でんき",
        "category": "物理",
        "pp": 15,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PAR": 1
            }
        ]
    },
    "がむしゃら": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "からげんき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ガリョウテンセイ": {
        "type": "ひこう",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1,
                "D": -1
            }
        ]
    },
    "かわらわり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 15,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "break_wall"
        ]
    },
    "がんせきアックス": {
        "type": "いわ",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "がんせきふうじ": {
        "type": "いわ",
        "category": "物理",
        "pp": 15,
        "power": 60,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "がんせきほう": {
        "type": "いわ",
        "category": "物理",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "bullet",
            "immovable"
        ]
    },
    "きあいパンチ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 150,
        "accuracy": 100,
        "priority": -3,
        "flags": [
            "contact",
            "non_negoto",
            "punch",
            "quick_charge"
        ]
    },
    "ギガインパクト": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "immovable"
        ]
    },
    "きしかいせい": {
        "type": "かくとう",
        "category": "物理",
        "pp": 15,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "きゅうけつ": {
        "type": "むし",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "きょけんとつげき": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "きょじゅうざん": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "きょじゅうだん": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "キラースピン": {
        "type": "どく",
        "category": "物理",
        "pp": 15,
        "power": 30,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "PSN": 1
            }
        ]
    },
    "きりさく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "high_critical"
        ]
    },
    "クイックターン": {
        "type": "みず",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "switch"
        ]
    },
    "くさわけ": {
        "type": "くさ",
        "category": "物理",
        "pp": 20,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "くちばしキャノン": {
        "type": "ひこう",
        "category": "物理",
        "pp": 15,
        "power": 100,
        "accuracy": 100,
        "priority": -3,
        "flags": [
            "bullet",
            "non_negoto",
            "quick_charge"
        ]
    },
    "くらいつく": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bite",
            "contact"
        ]
    },
    "グラススライダー": {
        "type": "くさ",
        "category": "物理",
        "pp": 20,
        "power": 55,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "クラブハンマー": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ]
    },
    "クロスサンダー": {
        "type": "でんき",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0
    },
    "クロスチョップ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ]
    },
    "クロスポイズン": {
        "type": "どく",
        "category": "物理",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PSN": 1
            }
        ]
    },
    "げきりん": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "rage"
        ]
    },
    "けたぐり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "こうげきしれい": {
        "type": "むし",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "high_critical"
        ]
    },
    "こうそくスピン": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 40,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "ゴーストダイブ": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "hide",
            "anti_protect"
        ]
    },
    "こおりのキバ": {
        "type": "こおり",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "flinch": 1
            }
        ]
    },
    "こおりのつぶて": {
        "type": "こおり",
        "category": "物理",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1
    },
    "ゴッドバード": {
        "type": "ひこう",
        "category": "物理",
        "pp": 5,
        "power": 140,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "charge",
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "このは": {
        "type": "くさ",
        "category": "物理",
        "pp": 40,
        "power": 40,
        "accuracy": 100,
        "priority": 0
    },
    "コメットパンチ": {
        "type": "はがね",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.2,
                "A": 1
            }
        ]
    },
    "ころがる": {
        "type": "いわ",
        "category": "物理",
        "pp": 20,
        "power": 30,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "サイコカッター": {
        "type": "エスパー",
        "category": "物理",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "slash",
            "high_critical"
        ]
    },
    "サイコファング": {
        "type": "エスパー",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bite",
            "contact",
            "break_wall"
        ]
    },
    "サイコブレイド": {
        "type": "エスパー",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "サンダーダイブ": {
        "type": "でんき",
        "category": "物理",
        "pp": 15,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_miss",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "ジェットパンチ": {
        "type": "みず",
        "category": "物理",
        "pp": 15,
        "power": 60,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "シェルブレード": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "B": -1
            }
        ]
    },
    "しおづけ": {
        "type": "いわ",
        "category": "物理",
        "pp": 15,
        "power": 40,
        "accuracy": 100,
        "priority": 0
    },
    "じごくづき": {
        "type": "あく",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "シザークロス": {
        "type": "むし",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "じしん": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 100,
        "priority": 0
    },
    "したでなめる": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 30,
        "power": 30,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "じたばた": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "じだんだ": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "しっぺがえし": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "じならし": {
        "type": "じめん",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "しねんのずつき": {
        "type": "エスパー",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "じばく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 200,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_before_move",
                "target": "self",
                "chance": 1,
                "recoil": 1
            }
        ]
    },
    "しめつける": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 15,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "bind",
            "contact"
        ]
    },
    "ジャイロボール": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet",
            "contact",
            "variable_power"
        ]
    },
    "シャドークロー": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 15,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ]
    },
    "シャドーダイブ": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "hide",
            "anti_protect"
        ]
    },
    "シャドーパンチ": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "じゃれつく": {
        "type": "フェアリー",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "A": -1
            }
        ]
    },
    "じわれ": {
        "type": "じめん",
        "category": "物理",
        "pp": 5,
        "power": 0,
        "accuracy": 30,
        "priority": 0,
        "flags": [
            "one_ko"
        ]
    },
    "しんそく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 80,
        "accuracy": 100,
        "priority": 2,
        "flags": [
            "contact"
        ]
    },
    "スイープビンタ": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 25,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_5"
        ]
    },
    "すいりゅうれんだ": {
        "type": "みず",
        "category": "物理",
        "pp": 5,
        "power": 25,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "critical",
            "punch",
            "combo_3_3"
        ]
    },
    "スケイルショット": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 20,
        "power": 25,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "combo_2_5"
        ]
    },
    "ずつき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "すてみタックル": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "ストーンエッジ": {
        "type": "いわ",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "high_critical"
        ]
    },
    "すなじごく": {
        "type": "じめん",
        "category": "物理",
        "pp": 15,
        "power": 35,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "bind"
        ]
    },
    "スパーク": {
        "type": "でんき",
        "category": "物理",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "スマートホーン": {
        "type": "はがね",
        "category": "物理",
        "pp": 10,
        "power": 70,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "せいなるつるぎ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "ignore_rank"
        ]
    },
    "せいなるほのお": {
        "type": "ほのお",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "BRN": 1
            }
        ]
    },
    "ソウルクラッシュ": {
        "type": "フェアリー",
        "category": "物理",
        "pp": 15,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "ソーラーブレード": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 125,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "charge",
            "contact",
            "slash",
            "solar"
        ]
    },
    "そらをとぶ": {
        "type": "ひこう",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact",
            "hide"
        ]
    },
    "たいあたり": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,
        priority=0,
        flags=["contact"],
    ),
    "だいばくはつ": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 250,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_before_move",
                "target": "self",
                "chance": 1,
                "recoil": 1
            }
        ]
    },
    "ダイビング": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "hide"
        ]
    },
    "だいふんげき": {
        "type": "ほのお",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "rage"
        ]
    },
    "ダイヤストーム": {
        "type": "いわ",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.5,
                "B": 2
            }
        ]
    },
    "たきのぼり": {
        "type": "みず",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "ダストシュート": {
        "type": "どく",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 80,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PSN": 1
            }
        ]
    },
    "たたきつける": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 80,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "タネばくだん": {
        "type": "くさ",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ]
    },
    "タネマシンガン": {
        "type": "くさ",
        "category": "物理",
        "pp": 30,
        "power": 25,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet",
            "combo_2_5"
        ]
    },
    "ダブルアタック": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 35,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_2"
        ]
    },
    "ダブルウイング": {
        "type": "ひこう",
        "category": "物理",
        "pp": 10,
        "power": 40,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_2"
        ]
    },
    "ダメおし": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "だんがいのつるぎ": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 85,
        "priority": 0
    },
    "ちきゅうなげ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ついばむ": {
        "type": "ひこう",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "つけあがる": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 20,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "つじぎり": {
        "type": "あく",
        "category": "物理",
        "pp": 15,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "high_critical"
        ]
    },
    "ツタこんぼう": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "high_critical"
        ]
    },
    "つつく": {
        "type": "ひこう",
        "category": "物理",
        "pp": 35,
        "power": 35,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "つっぱり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 15,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_5"
        ]
    },
    "つのでつく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 25,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "つのドリル": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 0,
        "accuracy": 30,
        "priority": 0,
        "flags": [
            "contact",
            "one_ko"
        ]
    },
    "つばさでうつ": {
        "type": "ひこう",
        "category": "物理",
        "pp": 35,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "つばめがえし": {
        "type": "ひこう",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "つららおとし": {
        "type": "こおり",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "つららばり": {
        "type": "こおり",
        "category": "物理",
        "pp": 30,
        "power": 25,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "combo_2_5"
        ]
    },
    "つるのムチ": {
        "type": "くさ",
        "category": "物理",
        "pp": 25,
        "power": 45,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "であいがしら": {
        "type": "むし",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 2,
        "flags": [
            "contact",
            "first_turn"
        ]
    },
    "デカハンマー": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 160,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unrepeatable"
        ]
    },
    "でんこうせっか": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "でんこうそうげき": {
        "type": "でんき",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "どくづき": {
        "type": "どく",
        "category": "物理",
        "pp": 20,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PSN": 1
            }
        ]
    },
    "どくどくのキバ": {
        "type": "どく",
        "category": "物理",
        "pp": 15,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "PSN": 2
            }
        ]
    },
    "どくばり": {
        "type": "どく",
        "category": "物理",
        "pp": 35,
        "power": 15,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PSN": 1
            }
        ]
    },
    "どくばりセンボン": {
        "type": "どく",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "PSN": 1
            }
        ]
    },
    "どげざつき": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ドゲザン": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "とっしん": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 90,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.25
            }
        ]
    },
    "とっておき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 140,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "とどめばり": {
        "type": "むし",
        "category": "物理",
        "pp": 25,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "とびかかる": {
        "type": "むし",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "A": -1
            }
        ]
    },
    "とびつく": {
        "type": "むし",
        "category": "物理",
        "pp": 20,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "とびはねる": {
        "type": "ひこう",
        "category": "物理",
        "pp": 5,
        "power": 85,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact",
            "hide"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "とびひざげり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 130,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_miss",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "ともえなげ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 90,
        "priority": -6,
        "flags": [
            "contact"
        ]
    },
    "ドラゴンアロー": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "combo_2_2"
        ]
    },
    "ドラゴンクロー": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ドラゴンダイブ": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "ドラゴンテール": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 90,
        "priority": -6,
        "flags": [
            "contact"
        ]
    },
    "ドラゴンハンマー": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ドラムアタック": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "トリックフラワー": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 70,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "critical"
        ]
    },
    "トリプルアクセル": {
        "type": "こおり",
        "category": "物理",
        "pp": 10,
        "power": 20,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "combo_3_3"
        ]
    },
    "トリプルキック": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 10,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "combo_3_3"
        ]
    },
    "トリプルダイブ": {
        "type": "みず",
        "category": "物理",
        "pp": 10,
        "power": 30,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact",
            "combo_3_3"
        ]
    },
    "ドリルくちばし": {
        "type": "ひこう",
        "category": "物理",
        "pp": 20,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ドリルライナー": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ]
    },
    "ドレインパンチ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "トロピカルキック": {
        "type": "くさ",
        "category": "物理",
        "pp": 15,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "A": -1
            }
        ]
    },
    "どろぼう": {
        "type": "あく",
        "category": "物理",
        "pp": 25,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "とんぼがえり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["contact"],
        handlers={Event.ON_HIT: Handler(hdl.pivot)}
    ),
    "なげつける": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "variable_power"
        ]
    },
    "にぎりつぶす": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "にどげり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 30,
        "power": 30,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_2"
        ]
    },
    "ニトロチャージ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 20,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "ねこだまし": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 40,
        "accuracy": 100,
        "priority": 3,
        "flags": [
            "contact",
            "first_turn"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "flinch": 1
            }
        ]
    },
    "ネコにこばん": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 40,
        "accuracy": 100,
        "priority": 0
    },
    "ネズミざん": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 20,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "combo_10_10"
        ]
    },
    "のしかかり": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "ハードプレス": {
        "type": "はがね",
        "category": "物理",
        "pp": 10,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "ハイパードリル": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "anti_protect"
        ]
    },
    "はいよるいちげき": {
        "type": "むし",
        "category": "物理",
        "pp": 10,
        "power": 70,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "ばかぢから": {
        "type": "かくとう",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "A": -1,
                "B": -1
            }
        ]
    },
    "はがねのつばさ": {
        "type": "はがね",
        "category": "物理",
        "pp": 25,
        "power": 70,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.1,
                "B": 1
            }
        ]
    },
    "ばくれつパンチ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 50,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "confusion": 1
            }
        ]
    },
    "ハサミギロチン": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 0,
        "accuracy": 30,
        "priority": 0,
        "flags": [
            "contact",
            "contact",
            "one_ko"
        ]
    },
    "はさむ": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 30,
        "power": 55,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "contact"
        ]
    },
    "はたきおとす": {
        "type": "あく",
        "category": "物理",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "contact"
        ]
    },
    "はたく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 35,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "contact"
        ]
    },
    "はっけい": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "はっぱカッター": {
        "type": "くさ",
        "category": "物理",
        "pp": 25,
        "power": 55,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "slash",
            "high_critical"
        ]
    },
    "はなふぶき": {
        "type": "くさ",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wind"
        ]
    },
    "はやてがえし": {
        "type": "かくとう",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 100,
        "priority": 3,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "flinch": 1
            }
        ]
    },
    "バリアーラッシュ": {
        "type": "エスパー",
        "category": "物理",
        "pp": 10,
        "power": 70,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": 1
            }
        ]
    },
    "バレットパンチ": {
        "type": "はがね",
        "category": "物理",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "パワーウィップ": {
        "type": "くさ",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "パワフルエッジ": {
        "type": "いわ",
        "category": "物理",
        "pp": 5,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "anti_protect"
        ]
    },
    "ヒートスタンプ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 10,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "ひけん・ちえなみ": {
        "type": "あく",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ひっかく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 35,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ひょうざんおろし": {
        "type": "こおり",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 85,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "びりびりちくちく": {
        "type": "でんき",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "ふいうち": {
        "type": "あく",
        "category": "物理",
        "pp": 5,
        "power": 70,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact"
        ]
    },
    "フェイタルクロー": {
        "type": "どく",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "PSN": 1,
                "PAR": 1,
                "SLP": 1
            }
        ]
    },
    "フェイント": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 30,
        "accuracy": 100,
        "priority": 2,
        "flags": [
            "anti_protect"
        ]
    },
    "ふくろだたき": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0
    },
    "ぶちかまし": {
        "type": "じめん",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1,
                "D": -1
            }
        ]
    },
    "ふみつけ": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "フライングプレス": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "フリーズボルト": {
        "type": "こおり",
        "category": "物理",
        "pp": 5,
        "power": 140,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "charge"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "ブリザードランス": {
        "type": "こおり",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0
    },
    "フレアドライブ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 15,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "ブレイククロー": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "B": -1
            }
        ]
    },
    "ブレイズキック": {
        "type": "ほのお",
        "category": "物理",
        "pp": 10,
        "power": 85,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "ブレイブバード": {
        "type": "ひこう",
        "category": "物理",
        "pp": 15,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "プレゼント": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 0,
        "accuracy": 90,
        "priority": 0
    },
    "ふんどのこぶし": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "ぶんまわす": {
        "type": "あく",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ヘビーボンバー": {
        "type": "はがね",
        "category": "物理",
        "pp": 10,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "ホイールスピン": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": -2
            }
        ]
    },
    "ポイズンテール": {
        "type": "どく",
        "category": "物理",
        "pp": 25,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PSN": 1
            }
        ]
    },
    "ほうふく": {
        "type": "あく",
        "category": "物理",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ボーンラッシュ": {
        "type": "じめん",
        "category": "物理",
        "pp": 10,
        "power": 25,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "combo_2_5"
        ]
    },
    "ほしがる": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 25,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ほっぺすりすり": {
        "type": "でんき",
        "category": "物理",
        "pp": 20,
        "power": 20,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "PAR": 1
            }
        ]
    },
    "ボディプレス": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ほのおのキバ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 15,
        "power": 65,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "flinch": 1
            }
        ]
    },
    "ほのおのパンチ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 15,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "ほのおのムチ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "B": -1
            }
        ]
    },
    "ポルターガイスト": {
        "type": "ゴースト",
        "category": "物理",
        "pp": 5,
        "power": 110,
        "accuracy": 90,
        "priority": 0
    },
    "ボルテッカー": {
        "type": "でんき",
        "category": "物理",
        "pp": 15,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.33
            }
        ]
    },
    "まきつく": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 15,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "bind",
            "contact"
        ]
    },
    "マッハパンチ": {
        "type": "かくとう",
        "category": "物理",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "ミサイルばり": {
        "type": "むし",
        "category": "物理",
        "pp": 20,
        "power": 25,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "combo_2_5"
        ]
    },
    "みだれづき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 15,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_5"
        ]
    },
    "みだれひっかき": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 15,
        "power": 18,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "contact",
            "combo_2_5"
        ]
    },
    "みねうち": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 40,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "むしくい": {
        "type": "むし",
        "category": "物理",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "むねんのつるぎ": {
        "type": "ほのお",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "メガトンキック": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 5,
        "power": 120,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "メガトンパンチ": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 20,
        "power": 80,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ]
    },
    "メガホーン": {
        "type": "むし",
        "category": "物理",
        "pp": 10,
        "power": 120,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "メタルクロー": {
        "type": "はがね",
        "category": "物理",
        "pp": 35,
        "power": 50,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.1,
                "A": 1
            }
        ]
    },
    "メタルバースト": {
        "type": "はがね",
        "category": "物理",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0
    },
    "メテオドライブ": {
        "type": "はがね",
        "category": "物理",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_ability"
        ]
    },
    "もろはのずつき": {
        "type": "いわ",
        "category": "物理",
        "pp": 5,
        "power": 150,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "やけっぱち": {
        "type": "ほのお",
        "category": "物理",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "ゆきなだれ": {
        "type": "こおり",
        "category": "物理",
        "pp": 10,
        "power": 60,
        "accuracy": 100,
        "priority": -4,
        "flags": [
            "contact"
        ]
    },
    "らいげき": {
        "type": "でんき",
        "category": "物理",
        "pp": 5,
        "power": 130,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "PAR": 1
            }
        ]
    },
    "らいめいげり": {
        "type": "かくとう",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "B": -1
            }
        ]
    },
    "リーフブレード": {
        "type": "くさ",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "slash",
            "high_critical"
        ]
    },
    "レイジングブル": {
        "type": "ノーマル",
        "category": "物理",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "break_wall"
        ]
    },
    "れいとうパンチ": {
        "type": "こおり",
        "category": "物理",
        "pp": 15,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "punch"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "れんぞくぎり": {
        "type": "むし",
        "category": "物理",
        "pp": 20,
        "power": 40,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "contact",
            "slash"
        ]
    },
    "ローキック": {
        "type": "かくとう",
        "category": "物理",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "ロックブラスト": {
        "type": "いわ",
        "category": "物理",
        "pp": 10,
        "power": 25,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "bullet",
            "combo_2_5"
        ]
    },
    "ワイドブレイカー": {
        "type": "ドラゴン",
        "category": "物理",
        "pp": 15,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "A": -1
            }
        ]
    },
    "ワイルドボルト": {
        "type": "でんき",
        "category": "物理",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "recoil": 0.25
            }
        ]
    },
    "わるあがき": MoveData(
        type="ステラ",
        category="物理",
        pp=999,
        power=40,
        flags=["contact", "non_encore"],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.modify_hp(b, c, "self", r=-1/4))}
    ),
    "１０まんボルト": {
        "type": "でんき",
        "category": "特殊",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0
    },
    "アーマーキャノン": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1,
                "D": -1
            }
        ]
    },
    "あおいほのお": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 130,
        "accuracy": 85,
        "priority": 0
    },
    "あくうせつだん": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "high_critical"
        ]
    },
    "あくのはどう": {
        "type": "あく",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wave"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "アシストパワー": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 20,
        "accuracy": 100,
        "priority": 0
    },
    "アシッドボム": {
        "type": "どく",
        "category": "特殊",
        "pp": 20,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "D": -2
            }
        ]
    },
    "アストラルビット": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0
    },
    "いじげんホール": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "anti_protect"
        ]
    },
    "いてつくしせん": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "イナズマドライブ": {
        "type": "でんき",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ]
    },
    "いにしえのうた": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "SLP": 1
            }
        ]
    },
    "いのちがけ": {
        "type": "かくとう",
        "category": "特殊",
        "pp": 5,
        "power": 0,
        "accuracy": 100,
        "priority": 0
    },
    "いびき": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 15,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound",
            "sleep"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "ウェザーボール": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ]
    },
    "うずしお": {
        "type": "みず",
        "category": "特殊",
        "pp": 15,
        "power": 35,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "bind"
        ]
    },
    "うたかたのアリア": {
        "type": "みず",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "うらみつらみ": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "A": -1
            }
        ]
    },
    "エアカッター": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 25,
        "power": 60,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "slash",
            "high_critical",
            "wind"
        ]
    },
    "エアスラッシュ": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 15,
        "power": 75,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "slash"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "flinch": 1
            }
        ]
    },
    "エアロブラスト": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "high_critical",
            "wind"
        ]
    },
    "エコーボイス": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 15,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "エナジーボール": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "エレキネット": {
        "type": "でんき",
        "category": "特殊",
        "pp": 15,
        "power": 55,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "エレキボール": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet",
            "variable_power"
        ]
    },
    "エレクトロビーム": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 130,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "charge"
        ]
    },
    "オーバードライブ": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "オーバーヒート": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 130,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": -2
            }
        ]
    },
    "オーラウイング": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "high_critical"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "S": 1
            }
        ]
    },
    "オーロラビーム": {
        "type": "こおり",
        "category": "特殊",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "A": -1
            }
        ]
    },
    "かえんほうしゃ": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "かぜおこし": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 35,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wind"
        ]
    },
    "カタストロフィ": {
        "type": "あく",
        "category": "特殊",
        "pp": 10,
        "power": 0,
        "accuracy": 90,
        "priority": 0
    },
    "かふんだんご": {
        "type": "むし",
        "category": "特殊",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ]
    },
    "かみなり": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 110,
        "accuracy": 70,
        "priority": 0,
        "flags": [
            "rainy_accuracy"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PAR": 1
            }
        ]
    },
    "かみなりあらし": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "rainy_accuracy",
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "PAR": 1
            }
        ]
    },
    "きあいだま": {
        "type": "かくとう",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 70,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "ギガドレイン": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "きまぐレーザー": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "くさのちかい": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "くさむすび": {
        "type": "くさ",
        "category": "特殊",
        "pp": 20,
        "power": 1,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "variable_power"
        ]
    },
    "クリアスモッグ": {
        "type": "どく",
        "category": "特殊",
        "pp": 15,
        "power": 50,
        "accuracy": 0,
        "priority": 0
    },
    "クロスフレイム": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unfreeze"
        ]
    },
    "クロロブラスト": {
        "type": "くさ",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_before_move",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "ゲップ": {
        "type": "どく",
        "category": "特殊",
        "pp": 10,
        "power": 120,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "non_negoto"
        ]
    },
    "げんしのちから": {
        "type": "いわ",
        "category": "特殊",
        "pp": 5,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.1,
                "A": 1,
                "B": 1,
                "C": 1,
                "D": 1,
                "S": 1
            }
        ]
    },
    "こおりのいぶき": {
        "type": "こおり",
        "category": "特殊",
        "pp": 10,
        "power": 60,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "critical"
        ]
    },
    "コールドフレア": {
        "type": "こおり",
        "category": "特殊",
        "pp": 5,
        "power": 140,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "charge"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "ゴールドラッシュ": {
        "type": "はがね",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "こがらしあらし": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 10,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "rainy_accuracy",
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "S": -1
            }
        ]
    },
    "こごえるかぜ": {
        "type": "こおり",
        "category": "特殊",
        "pp": 15,
        "power": 55,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "こごえるせかい": {
        "type": "こおり",
        "category": "特殊",
        "pp": 10,
        "power": 65,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "こなゆき": {
        "type": "こおり",
        "category": "特殊",
        "pp": 25,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "こんげんのはどう": {
        "type": "みず",
        "category": "特殊",
        "pp": 10,
        "power": 110,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "wave"
        ]
    },
    "サイケこうせん": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "confusion": 1
            }
        ]
    },
    "サイコキネシス": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "サイコショック": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "physical"
        ]
    },
    "サイコノイズ": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "サイコブースト": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 140,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": -2
            }
        ]
    },
    "サイコブレイク": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "physical"
        ]
    },
    "さばきのつぶて": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 100,
        "accuracy": 100,
        "priority": 0
    },
    "さわぐ": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "non_negoto",
            "sound"
        ]
    },
    "サンダープリズン": {
        "type": "でんき",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "bind"
        ]
    },
    "シードフレア": {
        "type": "くさ",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 85,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.4,
                "D": -2
            }
        ]
    },
    "シェルアームズ": {
        "type": "どく",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "PSN": 1
            }
        ]
    },
    "しおふき": {
        "type": "みず",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 100,
        "priority": 0
    },
    "しおみず": {
        "type": "みず",
        "category": "特殊",
        "pp": 10,
        "power": 65,
        "accuracy": 100,
        "priority": 0
    },
    "しっとのほのお": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 70,
        "accuracy": 100,
        "priority": 0
    },
    "シャカシャカほう": {
        "type": "くさ",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "シャドーボール": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "D": -1
            }
        ]
    },
    "シャドーレイ": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_ability"
        ]
    },
    "しんくうは": {
        "type": "かくとう",
        "category": "特殊",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 1
    },
    "じんつうりき": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 20,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "flinch": 1
            }
        ]
    },
    "しんぴのちから": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 70,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": 1
            }
        ]
    },
    "しんぴのつるぎ": {
        "type": "かくとう",
        "category": "特殊",
        "pp": 10,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "slash",
            "physical"
        ]
    },
    "じんらい": {
        "type": "でんき",
        "category": "特殊",
        "pp": 5,
        "power": 70,
        "accuracy": 100,
        "priority": 1
    },
    "すいとる": {
        "type": "くさ",
        "category": "特殊",
        "pp": 25,
        "power": 20,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "スケイルノイズ": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 110,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "B": -1
            }
        ]
    },
    "スチームバースト": {
        "type": "みず",
        "category": "特殊",
        "pp": 5,
        "power": 110,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "スピードスター": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 20,
        "power": 60,
        "accuracy": 0,
        "priority": 0
    },
    "スモッグ": {
        "type": "どく",
        "category": "特殊",
        "pp": 20,
        "power": 30,
        "accuracy": 70,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.4,
                "PSN": 1
            }
        ]
    },
    "ぜったいれいど": {
        "type": "こおり",
        "category": "特殊",
        "pp": 5,
        "power": 0,
        "accuracy": 30,
        "priority": 0,
        "flags": [
            "one_ko"
        ]
    },
    "ソーラービーム": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "charge",
            "solar"
        ]
    },
    "だいちのちから": {
        "type": "じめん",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "だいちのはどう": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wave"
        ]
    },
    "ダイマックスほう": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "non_encore",
            "non_negoto"
        ]
    },
    "だいもんじ": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 110,
        "accuracy": 85,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "タキオンカッター": {
        "type": "はがね",
        "category": "特殊",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "combo_2_2"
        ]
    },
    "だくりゅう": {
        "type": "みず",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 85,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "Hit": -1
            }
        ]
    },
    "たたりめ": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 10,
        "power": 65,
        "accuracy": 100,
        "priority": 0
    },
    "たつまき": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 20,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "チャージビーム": {
        "type": "でんき",
        "category": "特殊",
        "pp": 10,
        "power": 50,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.7,
                "C": 1
            }
        ]
    },
    "チャームボイス": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 15,
        "power": 40,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "ツインビーム": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "combo_2_2"
        ]
    },
    "てっていこうせん": {
        "type": "はがね",
        "category": "特殊",
        "pp": 5,
        "power": 140,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_before_move",
                "target": "self",
                "chance": 1,
                "recoil": 0.5
            }
        ]
    },
    "テラクラスター": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 5,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "terastal"
        ]
    },
    "テラバースト": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "terastal"
        ]
    },
    "でんきショック": {
        "type": "でんき",
        "category": "特殊",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PAR": 1
            }
        ]
    },
    "でんげきは": {
        "type": "でんき",
        "category": "特殊",
        "pp": 20,
        "power": 60,
        "accuracy": 0,
        "priority": 0
    },
    "でんじほう": MoveData(
        type="でんき",
        category="特殊",
        pp=5,
        power=120,
        accuracy=50,
        priority=0,
        flags=["bullet"],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.apply_ailment(b, c, "foe", "まひ"))}
    ),
    "ときのほうこう": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "トライアタック": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "PAR": 1,
                "BRN": 1,
                "FLZ": 1
            }
        ]
    },
    "ドラゴンエナジー": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 100,
        "priority": 0
    },
    "ドレインキッス": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 10,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.75
            }
        ]
    },
    "どろかけ": {
        "type": "じめん",
        "category": "特殊",
        "pp": 10,
        "power": 20,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "Hit": -1
            }
        ]
    },
    "ナイトバースト": {
        "type": "あく",
        "category": "特殊",
        "pp": 10,
        "power": 85,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.4,
                "Hit": -1
            }
        ]
    },
    "ナイトヘッド": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0
    },
    "なみのり": {
        "type": "みず",
        "category": "特殊",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0
    },
    "ねっさのあらし": {
        "type": "じめん",
        "category": "特殊",
        "pp": 10,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "rainy_accuracy",
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "BRN": 1
            }
        ]
    },
    "ねっさのだいち": {
        "type": "じめん",
        "category": "特殊",
        "pp": 10,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "ねっとう": {
        "type": "みず",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unfreeze"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "ねっぷう": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 10,
        "power": 95,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "ねらいうち": {
        "type": "みず",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "high_critical"
        ]
    },
    "ねんりき": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 25,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "confusion": 1
            }
        ]
    },
    "バークアウト": {
        "type": "あく",
        "category": "特殊",
        "pp": 15,
        "power": 55,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "sound"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "ハードプラント": {
        "type": "くさ",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "ハイドロカノン": {
        "type": "みず",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "ハイドロスチーム": {
        "type": "みず",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unfreeze"
        ]
    },
    "ハイドロポンプ": {
        "type": "みず",
        "category": "特殊",
        "pp": 5,
        "power": 110,
        "accuracy": 80,
        "priority": 0
    },
    "ハイパーボイス": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "はかいこうせん": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "はきだす": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0
    },
    "ばくおんぱ": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 10,
        "power": 140,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "はどうだん": {
        "type": "かくとう",
        "category": "特殊",
        "pp": 20,
        "power": 80,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "bullet",
            "wave"
        ]
    },
    "はなびらのまい": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "contact",
            "rage"
        ]
    },
    "バブルこうせん": {
        "type": "みず",
        "category": "特殊",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "S": -1
            }
        ]
    },
    "はめつのねがい": {
        "type": "はがね",
        "category": "特殊",
        "pp": 5,
        "power": 140,
        "accuracy": 100,
        "priority": 0
    },
    "パラボラチャージ": {
        "type": "でんき",
        "category": "特殊",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "はるのあらし": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 80,
        "priority": 0,
        "flags": [
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "A": -1
            }
        ]
    },
    "パワージェム": {
        "type": "いわ",
        "category": "特殊",
        "pp": 20,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "ひのこ": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 25,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "BRN": 1
            }
        ]
    },
    "ひゃっきやこう": {
        "type": "ゴースト",
        "category": "特殊",
        "pp": 15,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "ひやみず": {
        "type": "みず",
        "category": "特殊",
        "pp": 20,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "A": -1
            }
        ]
    },
    "フォトンゲイザー": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_ability"
        ]
    },
    "ぶきみなじゅもん": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "ふぶき": {
        "type": "こおり",
        "category": "特殊",
        "pp": 5,
        "power": 110,
        "accuracy": 70,
        "priority": 0,
        "flags": [
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "ブラストバーン": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "ブラッドムーン": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 5,
        "power": 140,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unrepeatable"
        ]
    },
    "フリーズドライ": {
        "type": "こおり",
        "category": "特殊",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "プリズムレーザー": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 160,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "immovable"
        ]
    },
    "フルールカノン": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 5,
        "power": 130,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1
            }
        ]
    },
    "フレアソング": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": 1
            }
        ]
    },
    "ふんえん": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "BRN": 1
            }
        ]
    },
    "ふんか": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 150,
        "accuracy": 100,
        "priority": 0
    },
    "ヘドロウェーブ": {
        "type": "どく",
        "category": "特殊",
        "pp": 10,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "PSN": 1
            }
        ]
    },
    "ヘドロこうげき": {
        "type": "どく",
        "category": "特殊",
        "pp": 20,
        "power": 65,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PSN": 1
            }
        ]
    },
    "ヘドロばくだん": {
        "type": "どく",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PSN": 1
            }
        ]
    },
    "ベノムショック": {
        "type": "どく",
        "category": "特殊",
        "pp": 10,
        "power": 65,
        "accuracy": 100,
        "priority": 0
    },
    "ほうでん": {
        "type": "でんき",
        "category": "特殊",
        "pp": 15,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "ぼうふう": {
        "type": "ひこう",
        "category": "特殊",
        "pp": 10,
        "power": 110,
        "accuracy": 70,
        "priority": 0,
        "flags": [
            "rainy_accuracy",
            "wind"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "confusion": 1
            }
        ]
    },
    "ほのおのうず": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 15,
        "power": 35,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "bind"
        ]
    },
    "ほのおのちかい": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "ほのおのまい": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 0.5,
                "C": 1
            }
        ]
    },
    "ボルトチェンジ": {
        "type": "でんき",
        "category": "特殊",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "switch"
        ]
    },
    "マグマストーム": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "bind"
        ]
    },
    "マジカルシャイン": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "マジカルフレイム": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 10,
        "power": 75,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "マジカルリーフ": {
        "type": "くさ",
        "category": "特殊",
        "pp": 20,
        "power": 60,
        "accuracy": 0,
        "priority": 0
    },
    "マッドショット": {
        "type": "じめん",
        "category": "特殊",
        "pp": 15,
        "power": 55,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "S": -1
            }
        ]
    },
    "まとわりつく": {
        "type": "むし",
        "category": "特殊",
        "pp": 20,
        "power": 20,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bind",
            "contact"
        ]
    },
    "みずあめボム": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 60,
        "accuracy": 85,
        "priority": 0
    },
    "みずしゅりけん": {
        "type": "みず",
        "category": "特殊",
        "pp": 20,
        "power": 15,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "combo_2_5"
        ]
    },
    "みずでっぽう": {
        "type": "みず",
        "category": "特殊",
        "pp": 25,
        "power": 40,
        "accuracy": 100,
        "priority": 0
    },
    "ミストバースト": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_before_move",
                "target": "self",
                "chance": 1,
                "recoil": 1
            }
        ]
    },
    "ミストボール": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "bullet"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "C": -1
            }
        ]
    },
    "みずのちかい": {
        "type": "みず",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "みずのはどう": {
        "type": "みず",
        "category": "特殊",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wave"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "confusion": 1
            }
        ]
    },
    "ミラーコート": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": -5
    },
    "みらいよち": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 120,
        "accuracy": 100,
        "priority": 0
    },
    "みわくのボイス": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "ムーンフォース": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 15,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "C": -1
            }
        ]
    },
    "むしのさざめき": {
        "type": "むし",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ],
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "むしのていこう": {
        "type": "むし",
        "category": "特殊",
        "pp": 20,
        "power": 50,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "C": -1
            }
        ]
    },
    "メガドレイン": {
        "type": "くさ",
        "category": "特殊",
        "pp": 15,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "めざめるダンス": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 15,
        "power": 90,
        "accuracy": 100,
        "priority": 0
    },
    "メテオビーム": {
        "type": "いわ",
        "category": "特殊",
        "pp": 10,
        "power": 120,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "charge"
        ]
    },
    "もえあがるいかり": {
        "type": "あく",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "flinch": 1
            }
        ]
    },
    "やきつくす": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 15,
        "power": 60,
        "accuracy": 100,
        "priority": 0
    },
    "ゆめくい": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 15,
        "power": 100,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "drain": 0.5
            }
        ]
    },
    "ようかいえき": {
        "type": "どく",
        "category": "特殊",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "ようせいのかぜ": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 30,
        "power": 40,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wind"
        ]
    },
    "ライジングボルト": {
        "type": "でんき",
        "category": "特殊",
        "pp": 20,
        "power": 70,
        "accuracy": 100,
        "priority": 0
    },
    "ラスターカノン": {
        "type": "はがね",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "D": -1
            }
        ]
    },
    "ラスターパージ": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 5,
        "power": 95,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.5,
                "D": -1
            }
        ]
    },
    "リーフストーム": {
        "type": "くさ",
        "category": "特殊",
        "pp": 5,
        "power": 130,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": -2
            }
        ]
    },
    "りゅうせいぐん": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 5,
        "power": 130,
        "accuracy": 90,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "self",
                "chance": 1,
                "C": -2
            }
        ]
    },
    "りゅうのいぶき": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 20,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.3,
                "PAR": 1
            }
        ]
    },
    "りゅうのはどう": {
        "type": "ドラゴン",
        "category": "特殊",
        "pp": 10,
        "power": 85,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "wave"
        ]
    },
    "りんごさん": {
        "type": "くさ",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "D": -1
            }
        ]
    },
    "りんしょう": {
        "type": "ノーマル",
        "category": "特殊",
        "pp": 15,
        "power": 60,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "sound"
        ]
    },
    "ルミナコリジョン": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "D": -2
            }
        ]
    },
    "れいとうビーム": {
        "type": "こおり",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 100,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.1,
                "FLZ": 1
            }
        ]
    },
    "れんごく": {
        "type": "ほのお",
        "category": "特殊",
        "pp": 5,
        "power": 100,
        "accuracy": 50,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 1,
                "BRN": 1
            }
        ]
    },
    "ワイドフォース": {
        "type": "エスパー",
        "category": "特殊",
        "pp": 10,
        "power": 80,
        "accuracy": 100,
        "priority": 0
    },
    "ワンダースチーム": {
        "type": "フェアリー",
        "category": "特殊",
        "pp": 10,
        "power": 90,
        "accuracy": 95,
        "priority": 0,
        "effects": [
            {
                "trigger": "on_accuracy",
                "target": "opponent",
                "chance": 0.2,
                "confusion": 1
            }
        ]
    },
    "アクアリング": {
        "type": "みず",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "あくび": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "あくまのキッス": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "あさのひざし": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "あまいかおり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "あまえる": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "あまごい": {
        "type": "みず",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "あやしいひかり": {
        "type": "ゴースト",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "アロマセラピー": {
        "type": "くさ",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "アロマミスト": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "アンコール": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "non_encore"
        ]
    },
    "いえき": {
        "type": "どく",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "いかりのこな": {
        "type": "むし",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 2,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "いたみわけ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "いちゃもん": {
        "type": "あく",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "いとをはく": {
        "type": "むし",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 95,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "いのちのしずく": {
        "type": "みず",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "いばる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "いやしのすず": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "sound"
        ]
    },
    "いやしのねがい": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "いやしのはどう": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "heal"
        ]
    },
    "いやなおと": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "うそなき": {
        "type": "あく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "うたう": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 55,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "うつしえ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold"
        ]
    },
    "うらみ": {
        "type": "ゴースト",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "エレキフィールド": {
        "type": "でんき",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "えんまく": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "おいかぜ": {
        "type": "ひこう",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "wind"
        ]
    },
    "おいわい": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "non_negoto"
        ]
    },
    "オーロラベール": {
        "type": "こおり",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "おかたづけ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "おきみやげ": {
        "type": "あく",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "おさきにどうぞ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "おたけび": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "おだてる": {
        "type": "あく",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "おちゃかい": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "おにび": {
        "type": "ほのお",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ガードシェア": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "ガードスワップ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "かいでんぱ": {
        "type": "でんき",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "かいふくふうじ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "かえんのまもり": {
        "type": "ほのお",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "かげぶんしん": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "かたくなる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "かなしばり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "からにこもる": {
        "type": "みず",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "からをやぶる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "きあいだめ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ギアチェンジ": {
        "type": "はがね",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "キノコのほうし": {
        "type": "くさ",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "powder"
        ]
    },
    "きりばらい": {
        "type": "ひこう",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "きんぞくおん": {
        "type": "はがね",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 85,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "くすぐる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "グラスフィールド": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "くろいきり": {
        "type": "こおり",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "くろいまなざし": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "こうごうせい": {
        "type": "くさ",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "こうそくいどう": {
        "type": "エスパー",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "コーチング": {
        "type": "かくとう",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "コートチェンジ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 100,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "コスモパワー": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "コットンガード": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "このゆびとまれ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 2,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "こらえる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "こわいかお": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "さいきのいのり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 0,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "サイコフィールド": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "サイドチェンジ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 2,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "さいはい": {
        "type": "エスパー",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "さいみんじゅつ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 60,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "さきおくり": {
        "type": "あく",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "さむいギャグ": {
        "type": "こおり",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "switch"
        ]
    },
    "じこあんじ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "じこさいせい": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "しっぽきり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "switch"
        ]
    },
    "しっぽをふる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "じばそうさ": {
        "type": "でんき",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable"
        ]
    },
    "しびれごな": {
        "type": "くさ",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "powder"
        ]
    },
    "ジャングルヒール": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "じゅうでん": {
        "type": "でんき",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "じゅうりょく": {
        "type": "エスパー",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "しょうりのまい": {
        "type": "かくとう",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "しろいきり": {
        "type": "こおり",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "しんぴのまもり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 25,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "シンプルビーム": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "スキルスワップ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "スケッチ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 0,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "non_encore",
            "non_negoto"
        ]
    },
    "すてゼリフ": {
        "type": "あく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound",
            "switch"
        ]
    },
    "ステルスロック": {
        "type": "いわ",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "reflectable"
        ]
    },
    "すなあつめ": {
        "type": "じめん",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "すなあらし": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        flags=[
            "unprotectable",
            "ignore_substitute",
            "wind"
        ],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.apply_weather(b, c, "すなあらし"))}
    ),
    "すなかけ": {
        "type": "じめん",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "スピードスワップ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "すりかえ": {
        "type": "あく",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "スレッドトラップ": {
        "type": "むし",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "せいちょう": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ソウルビート": {
        "type": "ドラゴン",
        "category": "変化",
        "pp": 100,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "sound"
        ]
    },
    "ダークホール": {
        "type": "あく",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 50,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "タールショット": {
        "type": "いわ",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "たくわえる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "たてこもる": {
        "type": "はがね",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "タマゴうみ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "ちいさくなる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ちからをすいとる": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "heal"
        ]
    },
    "ちょうおんぱ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 55,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "ちょうのまい": {
        "type": "むし",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ちょうはつ": {
        "type": "あく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "つきのひかり": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "つぶらなひとみ": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 100,
        "priority": 1,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "つぼをつく": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "つめとぎ": {
        "type": "あく",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "つるぎのまい": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        flags=[
            "unprotectable",
            "ignore_substitute"
        ],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.modify_stat(b, c, "self", "A", +2))}
    ),
    "テクスチャー": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "テクスチャー２": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable"
        ]
    },
    "デコレーション": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "てだすけ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 5,
        "flags": [
            "unprotectable"
        ]
    },
    "てっぺき": {
        "type": "はがね",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "テレポート": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": -6,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "switch"
        ]
    },
    "てんしのキッス": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "でんじは": {
        "type": "でんき",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "でんじふゆう": {
        "type": "でんき",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "とおせんぼう": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "トーチカ": {
        "type": "どく",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "とおぼえ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "sound"
        ]
    },
    "どくガス": {
        "type": "どく",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "どくどく": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=90,
        flags=[
            "blocked_by_gold",
            "reflectable"
        ],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.apply_ailment(b, c, "foe", "もうどく"))}
    ),
    "どくのいと": {
        "type": "どく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "どくのこな": {
        "type": "どく",
        "category": "変化",
        "pp": 35,
        "power": 0,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "powder"
        ]
    },
    "どくびし": {
        "type": "どく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "reflectable"
        ]
    },
    "とぐろをまく": {
        "type": "どく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "とける": {
        "type": "どく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ドラゴンエール": {
        "type": "ドラゴン",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "トリック": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "トリックルーム": {
        "type": "エスパー",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": -7,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ドわすれ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ないしょばなし": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "なかまづくり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "なかよくする": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "なきごえ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "sound"
        ]
    },
    "なまける": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "なみだめ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "なやみのタネ": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "なりきり": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold"
        ]
    },
    "ニードルガード": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "にほんばれ": {
        "type": "ほのお",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "にらみつける": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ねがいごと": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "ねごと": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "non_encore",
            "non_negoto",
            "call_move",
            "sleep"
        ]
    },
    "ねばねばネット": {
        "type": "むし",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ねむりごな": {
        "type": "くさ",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 75,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "powder"
        ]
    },
    "ねむる": {
        "type": "エスパー",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "ねをはる": {
        "type": "くさ",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "のみこむ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "のろい": {
        "type": "ゴースト",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "ハートスワップ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "はいすいのじん": {
        "type": "かくとう",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ハッピータイム": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "バトンタッチ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "switch"
        ]
    },
    "はねやすめ": {
        "type": "ひこう",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "はねる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        flags=[
            "unprotectable",
            "ignore_substitute"
        ]
    ),
    "ハバネロエキス": {
        "type": "くさ",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "はらだいこ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "パワーシェア": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "パワースワップ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "パワートリック": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "ひかりのかべ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ひっくりかえす": {
        "type": "あく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ビルドアップ": {
        "type": "かくとう",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ファストガード": {
        "type": "かくとう",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 3,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "ふういん": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "フェアリーロック": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "フェザーダンス": {
        "type": "ひこう",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ふきとばし": MoveData(
        type="ノーマル",
        category="特殊",
        pp=20,
        priority=-6,
        flags=[
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable",
            "wind",
        ],
        handlers={Event.ON_HIT: Handler(hdl.blow)}
    ),
    "フラフラダンス": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold"
        ]
    },
    "フラワーヒール": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "blocked_by_gold",
            "reflectable",
            "heal"
        ]
    },
    "ふるいたてる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ブレイブチャージ": {
        "type": "エスパー",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "へびにらみ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 30,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "へんしん": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold",
            "non_encore"
        ]
    },
    "ぼうぎょしれい": {
        "type": "むし",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ほえる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": -6,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "reflectable",
            "sound"
        ]
    },
    "ほおばる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ほたるび": {
        "type": "むし",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ほろびのうた": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "blocked_by_gold",
            "sound"
        ]
    },
    "まきびし": {
        "type": "じめん",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "reflectable"
        ]
    },
    "マジックルーム": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "まねっこ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "non_negoto",
            "call_move"
        ]
    },
    "まほうのこな": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "まもる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "まるくなる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "みかづきのいのり": {
        "type": "エスパー",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "みかづきのまい": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "みがわり": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "みきり": {
        "type": "かくとう",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 4,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "protect"
        ]
    },
    "ミストフィールド": {
        "type": "フェアリー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "みずびたし": {
        "type": "みず",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "みちづれ": {
        "type": "ゴースト",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ミラータイプ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold"
        ]
    },
    "ミルクのみ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "heal"
        ]
    },
    "みをけずる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "めいそう": {
        "type": "エスパー",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "メロメロ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 15,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "ignore_substitute",
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ものまね": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "non_encore",
            "non_negoto",
            "call_move"
        ]
    },
    "もりののろい": {
        "type": "くさ",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "やどりぎのタネ": {
        "type": "くさ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 90,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable"
        ]
    },
    "ゆきげしき": {
        "type": "こおり",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ゆびをふる": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute",
            "non_negoto",
            "call_move"
        ]
    },
    "リサイクル": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "リフレクター": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        flags=[
            "unprotectable",
            "ignore_substitute"
        ],
        handlers={Event.ON_HIT: Handler(
            lambda b, c, v: common.apply_side(
                b, c, "self", "reflector", count=5, extended_count=8))}
    ),
    "リフレッシュ": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "りゅうのまい": {
        "type": "ドラゴン",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ロックオン": {
        "type": "ノーマル",
        "category": "変化",
        "pp": 5,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "ignore_substitute"
        ]
    },
    "ロックカット": {
        "type": "いわ",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ワイドガード": {
        "type": "いわ",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 3,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "わたほうし": {
        "type": "くさ",
        "category": "変化",
        "pp": 40,
        "power": 0,
        "accuracy": 100,
        "priority": 0,
        "flags": [
            "blocked_by_gold",
            "reflectable",
            "powder"
        ]
    },
    "わるだくみ": {
        "type": "あく",
        "category": "変化",
        "pp": 20,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    },
    "ワンダールーム": {
        "type": "エスパー",
        "category": "変化",
        "pp": 10,
        "power": 0,
        "accuracy": 0,
        "priority": 0,
        "flags": [
            "unprotectable",
            "ignore_substitute"
        ]
    }
}


# 共通ハンドラを追加
for name, obj in MOVES.items():
    if isinstance(obj, dict):
        continue
    MOVES[name].handlers |= {
        Event.ON_DECLARE_MOVE: Handler(hdl.reveal_move),
        Event.ON_CONSUME_PP: Handler(hdl.consume_pp),
    }
