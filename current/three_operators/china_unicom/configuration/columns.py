#coding=utf-8

# 表名
TABEL_NAME_1 = 't_operator_user'
TABLE_NAME_2 = 't_operator_call'

KEY_CONVERT_USER = {
    'custname': 'name',
    'custsex': 'sex',
    'certaddr': 'address',
    'certtype': 'cert_type',
    'certnum': 'cert_num',
    'productname': 'product_name',
    'custlvl': 'level',
    'opendate': 'open_date',
}

KEY_CONVERT_CALL = {
    'homeareaName': 'call_area',
    'calldate': 'call_date',
    'calltime': 'call_time',
    'totalfee':  'call_cost',
    'calllonghour': 'call_long',
    'othernum': 'other_phone',
    'calltypeName': 'call_type',
    'landtype': 'land_type'
}

COLUMN_USER = (
    'name','sex', 'address', 'cert_type', 'cert_num',
    'phone', 'company', 'province', 'city', 'product_name',
    'level', 'open_date', 'balance', 'user_valid'
)

COLUMN_CALL = (
    'cert_num', 'phone', 'call_area', 'call_date', 'call_time',
    'call_cost', 'call_long', 'other_phone', 'call_type', 'land_type'
)





