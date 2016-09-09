#coding=utf-8

"""
valid_keys 表示 json keys 映射到 t_shixin_valid 相应的columns

valid_columns 对应 t_shixin_valid 的columns
invalid_columns 对应 t_shixin_invalid 的columns
"""

valid_keys = {
    'id': 'sys_id',
    'iname': 'name',
    'age': 'age',
    'sexy': 'sex',
    'cardNum':'card_num',
    'businessEntity': 'business_entity',
    'areaName': 'area_name',
    'caseCode': 'case_code',
    'regDate': 'reg_date',
    'publishDate': 'publish_date',
    'gistId': 'gist_id',
    'courtName': 'court_name',
    'gistUnit': 'gist_unit',
    'duty': 'duty',
    'performance': 'performance',
    'disruptTypeName': 'disrupt_type_name',
    'partyTypeName': 'party_type_name'
}

valid_columns = valid_keys.values()
valid_columns.append('flag')

invalid_columns = ('sys_id', 'err_type')


