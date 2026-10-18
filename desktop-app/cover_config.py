"""Portable, optional cover preferences. No database or rendering authority here."""
import copy
import json
import math
import re

DEFAULTS = {
    'version': 1, 'style': 'auto', 'template': 'auto', 'seed': 0,
    'palette': 'auto', 'primary': '', 'customTitle': '', 'customSubtitle': '',
    'titlePosition': 'auto', 'density': 'balanced', 'imageSource': 'auto',
    'imageFit': 'fill', 'imageX': 50, 'imageY': 50,
}
ENUMS = {
    'style': ('auto', 'editorial', 'spatial', 'developer', 'kinetic', 'minimal', 'v5'),
    'template': ('auto', 'a', 'b', 'c'),
    'palette': ('auto', 'acid', 'paper', 'violet', 'cyan', 'coral', 'ink'),
    'titlePosition': ('auto', 'top', 'center', 'bottom'),
    'density': ('balanced', 'compact', 'bold'),
    'imageSource': ('auto', 'image', 'website', 'poster'),
    'imageFit': ('fill', 'fit'),
}


def _json_value(value, depth=1):
    if depth > 4:
        raise ValueError('封面设置层级过深')
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError('封面设置键名无效')
            _json_value(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _json_value(child, depth + 1)
    elif value is None or isinstance(value, (str, bool)):
        return
    elif type(value) in (int, float) and math.isfinite(value):
        return
    else:
        raise ValueError('封面设置必须是有限 JSON 数据')


def normalize_config(value):
    """None resets to auto; preserve bounded unknown/future data on roundtrip."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('封面设置必须是对象')
    _json_value(value)
    try:
        size = len(json.dumps(value, ensure_ascii=False, separators=(',', ':'),
                              allow_nan=False).encode('utf-8'))
    except (ValueError, UnicodeError, OverflowError) as exc:
        raise ValueError('封面设置不是有效 JSON') from exc
    if size > 8192:
        raise ValueError('封面设置超过 8 KiB')
    version = value.get('version', 1)
    if type(version) not in (int, float) or version != int(version) or not 1 <= version <= 2147483647:
        raise ValueError('封面设置版本无效')
    if version > 1:
        return copy.deepcopy(value)
    result = {**DEFAULTS, **copy.deepcopy(value)}
    for key, options in ENUMS.items():
        if result[key] not in options:
            raise ValueError('封面选项无效：' + key)
    seed = result['seed']
    if type(seed) not in (int, float) or seed != int(seed) or not 0 <= seed <= 4294967295:
        raise ValueError('封面种子无效')
    for key, maximum in (('customTitle', 200), ('customSubtitle', 240)):
        if not isinstance(result[key], str) or len(result[key]) > maximum:
            raise ValueError('封面文字无效：' + key)
    primary = result['primary']
    if not isinstance(primary, str) or (primary and not re.fullmatch(r'#[0-9a-fA-F]{6}', primary)):
        raise ValueError('封面主色必须是六位十六进制颜色')
    result['primary'] = primary.lower()
    for key in ('imageX', 'imageY'):
        if type(result[key]) not in (int, float) or not 0 <= result[key] <= 100:
            raise ValueError('封面图片位置无效')
    # Include canonical defaults in the persisted size bound, too.
    if len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > 8192:
        raise ValueError('封面设置超过 8 KiB')
    return result
