import pymysql

def db_connection():
    conn = pymysql.connect(
        host='localhost',
        db='test',
        user='root',
        password=''
    )
    return conn