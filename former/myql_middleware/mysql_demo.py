#coding=utf-8

'''
问题：
由于在爬取的过程中有些字段是不存在的,
所以每个字典（行）的内容是不一样的,
故无法用写死的sql语句有执行插入。
方案：
而是要根据字典的key(字段名),动态生成sql语句
'''
__author__ = 'moyh'
__date__ = '7/28'

def insertTest(item):

    column_names = ('stu_id', 'stu_name', 'stu_phone','stu_address', 'stu_remark')  # 表的列名

    columns = tuple(item.keys())    # 要插入字典的keys

    if set(columns) < set(column_names):    # 字典keys是否存在未知列名

        import MySQLdb
        conn = MySQLdb.connect(host='localhost',user='root',passwd='mysql2016',db='spider',charset='utf8')
        cur = conn.cursor()

        # 根据列名构造行
        row = list()
        for column in columns:
            row.append(item[column])
        # for

        # 构造%s
        flag = ('%s,'*len(columns)).rstrip(',')

        # 拼凑sql
        sql = 'insert into t_test{0}{1}{2}'.format('(', ','.join(columns), ')') + ' values{0}{1}{2}'.format('(', flag, ')')

        cur.execute(sql,row)
        conn.commit()
        cur.close()
        conn.close()
    else:
        raise KeyError('要插入的字典存在未知列名')



if __name__ == '__main__':

    item1 = dict(stu_id=111, stu_name='mo_yihua')
    item2 = dict(stu_id=222, stu_name='xiaoming', stu_phone='1580202022')
    item3 = dict(stu_id=333, stu_name='xiaofang', stu_phone='0202222222', stu_address='人民东路')
    item_list = list()
    item_list.extend([item1, item2, item3])
    for item in item_list:
        insertTest(item)


