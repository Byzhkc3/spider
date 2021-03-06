#coding=utf-8

# '台湾' '香港特别行政区' '澳门特别行政区'
_ROOT_NODE = {
    '北京市': '北京',
    '天津市': '天津',
    '上海市': '上海',
    '重庆市': '重庆',

    '河北省': '河北',
    '山西省': '山西',
    '辽宁省': '辽宁',
    '吉林省': '吉林',
    '黑龙江省': '黑龙江',
    '江苏省': '江苏',
    '浙江省': '浙江',
    '安徽省': '安徽',
    '福建省': '福建',
    '江西省': '江西',
    '山东省': '山东',
    '河南省': '河南',
    '湖北省': '湖北',
    '湖南省': '湖南',
    '广东省': '广东',
    '海南省': '海南',
    '四川省': '四川',
    '贵州省': '贵州',
    '云南省': '云南',
    '陕西省': '陕西',
    '甘肃省': '甘肃',
    '青海省': '青海',

    '广西壮族自治区': '广西',
    '内蒙古自治区': '内蒙古',
    '西藏自治区': '西藏',
    '宁夏回族自治区': '宁夏',
    '新疆维吾尔自治区': '新疆'
}

ROOT_DETAIL_NAMES = _ROOT_NODE.keys()
ROOT_SHORT_NAMES = _ROOT_NODE.values()
ROOT_CITY  = ('北京市', '天津市', '上海市', '重庆市')
ROOT_PROVINCE = tuple(set(ROOT_DETAIL_NAMES) - set(ROOT_CITY))

if __name__ == '__main__':
    print len(ROOT_SHORT_NAMES) #31
    # for i,v in enumerate(root_province):
    #     print i+1, v