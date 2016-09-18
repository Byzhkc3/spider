#coding=utf-8
import MySQLdb
import _mysql_exceptions


def getDBConnection():

    conn = MySQLdb.connect(host='localhost', user='root',
                               passwd='mysql2016', db='spider', charset='utf8')
    return conn

# end


def insertDicts(table_name, column_names, items):
    '''
    :param table_name: 表名
    :param column_names: 列名(不包括自增的列)
    :param items: 字典列表
    :return:
    '''

    if not isinstance(items, (list,tuple)):
        raise ValueError

    rows = list()
    conn = getDBConnection()

    for item in items:
        temp = list()
        for key in column_names:
            if key in item.keys():
                temp.append(item[key])
            else:
                temp.append('')
        rows.append(temp)

    # 构造%s
    symbol = ('%s,' * len(column_names)).rstrip(',')

    sql = 'insert into {table_name}({columms})'.\
          format(table_name=table_name, columms=','.join(column_names)) \
          +' values ({symbol})'.format(symbol=symbol)

    cur = conn.cursor()
    try:

        cur.executemany(sql, rows)
    except _mysql_exceptions.IntegrityError:
        for row in rows:
            try:
                cur.execute(sql, row)
            except _mysql_exceptions.IntegrityError:
                pass
            except Exception as ex:
                print ex,row
    except Exception as ex:
        print ex
    finally:
        conn.commit()
        cur.close()
        conn.close()
# end


def test_insertDicts(row_num):

    import time
    table_name = 't_test'
    column_names = ('stu_id', 'stu_name', 'stu_phone', 'stu_address', 'stu_remark')
    items = [dict(stu_id=i, stu_name='name'.format(i)) for i in range(row_num)]

    t_begin = time.time()
    insertDicts(table_name, column_names, items)
    print '结束：插入{row_num}条记录花费时间{time}'.format(row_num=row_num, time=time.time()-t_begin)


if __name__ == '__main__':
    # 10万数据大约需要4s
    test_insertDicts(100000)

