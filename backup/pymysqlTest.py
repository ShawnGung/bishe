import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='url_data', charset='utf8')
cursor = conn.cursor()
#effect_row = cursor.execute("insert into url(url)values(%s)", [("www.baidu.com")])
effect_row = cursor.execute("delete from url where num = " + str(1))
conn.commit()
cursor.close()
conn.close()
