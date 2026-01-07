from copy import deepcopy


def fast_copy(old, new, keys_to_deepcopy: list[str] | None = None):
    """指定されたkeyのみdeep copyし、それ以外はshallow copyする"""
    for key, val in old.__dict__.items():
        if keys_to_deepcopy and key in keys_to_deepcopy:
            setattr(new, key, deepcopy(val))
        else:
            setattr(new, key, recursive_copy(val))
    return new


def recursive_copy(obj):
    """オブジェクトを再帰的にコピーする"""
    if isinstance(obj, list):
        return [recursive_copy(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: recursive_copy(v) for k, v in obj.items()}
    else:
        return obj
