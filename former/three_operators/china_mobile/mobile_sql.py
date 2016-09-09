#coding=utf-8
import MySQLdb


def getDbConnect():
    return MySQLdb.connect(host='localhost', user='root', passwd='mysql2016', db='spider', charset='utf8')

# end

def t_china_mobile_user_insert(row):  # _mysql_exceptions.IntegrityError

    conn = getDbConnect()
    cur = conn.cursor()

    try:
        insert_sql = 'INSERT INTO t_china_mobile_user(phone, name,' \
                     'cert_id, puk_id, open_date, end_date) VALUES (%s, %s, %s, %s, %s, %s)'

        cur.execute(insert_sql, row)
        conn.commit()

    except Exception as ex:
        print ex
        return dict(result=False, error='t_china_mobile_user_insert{0}'.format(ex))

    else:
        print '插入用户数据成功'
        return dict(result=True,error='t_china_mobile_user_insert{0}'.format('no error'))

    finally:
        cur.close()
        conn.close()

# end


def t_china_mobile_call_insert(rows):

    conn = getDbConnect()
    cur = conn.cursor()

    try:
        insert_sql = 'INSERT INTO t_china_mobile_call ' \
                     '(cert_id,' \
                     ' phone, call_area, call_date, call_time, call_cost, call_long, ' \
                     'other_phone, call_type, land_type) ' \
                     'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

        cur.executemany(insert_sql, rows)
        conn.commit()

    except Exception as ex:
        print '批量插入通话记录失败'
        return dict(result=False, error='t_china_mobile_call_insert{0}'.format(ex))

    else:
        print '插入通话记录数据成功'
        return dict(result=True,error='t_china_mobile_call_insert{0}'.format('no error'))

    finally:
        cur.close()
        conn.close()

# end



