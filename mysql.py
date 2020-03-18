import pymysql, time
from pymysql.err import Error, OperationalError
from settings import SQL_SETTINGS
from Format import net_check, time_now, sleep
from logger import get_logger

logger = get_logger("sql")


class Sql():
    def __init__(self, **kwargs):
        # print(time_now() + " 数据库连接")
        while True:
            try:
                self.con = pymysql.connect(**kwargs)
            except Exception as e:
                print(e)
                # self.con.close()
                time.sleep(60)
            else:
                break
        self.cursor = self.con.cursor()
        self.cursor_dict = self.con.cursor(cursor=pymysql.cursors.DictCursor)

    def __del__(self):
        # print(time_now() + " 关闭数据库")
        self.con.close()

    def insert_new_data(self, table_name, **kwargs):
        sql = self.insert_new_data_sql(table_name, **kwargs)
        try:
            self.cursor.execute(sql, tuple(kwargs.values()))
        except Exception as e:
            self.con.rollback()
            return str(e) + "\n" + str(sql)
        else:
            self.con.commit()
            return None

    def update_old_data(self, table_name, dict1, dict2):
        sql = self.update_old_data_sql(table_name, dict1, dict2)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.con.rollback()
            return str(e) + "\n" + str(sql)
        else:
            self.con.commit()
            return None

    def select_data(self, table_name, limit_num, *args, **kwargs):
        sql = self.select_data_sql(table_name, limit_num, *args, **kwargs)
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        return res

    def delete_data(self, table_name, **kwargs):
        sql = self.delete_data_sql(table_name, **kwargs)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.con.rollback()
            return str(e) + "\n" + str(sql)
        else:
            self.con.commit()
            return None

    def concat(self, dictionary, string):
        """
        拼装字典
        :param dictionary: 需要拼装的字典
        :param string: 拼装时所使用的连接的字符
        :return: key='value' string key='value' string key='value'...
        """
        for k, v in dictionary.items():
            dictionary[k] = str(v)
        list_key_value = []
        for k, v in dictionary.items():
            list_key_value.append(k + "=" + '\'' + v + '\'')
        conditions = string.join(list_key_value)
        return conditions

    def insert_new_data_sql(self, table_name, **kwargs):
        keys = ','.join(kwargs.keys())
        values = ','.join(['%s'] * len(kwargs))
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table_name, keys, values)
        return sql

    def select_data_sql(self, table_name, limit_num, *args, **kwargs):
        """
        :param table_name: 操作的表名
        :param limit_num:查询结果输出的条数
        :param args: 需要查询的表头数组
        :param kwargs: 查询条件的字典
        :return: 查询结果
        """
        table_head = ",".join(args)
        if kwargs:
            a = self.concat(kwargs, " AND ")
            where_string = " where %s" % (a)
        else:
            where_string = ""
        if limit_num != 0:
            limit = " limit %d" % limit_num
        else:
            limit = ""
        sql = "select %s from %s%s%s" % (table_head, table_name, where_string, limit)
        return sql

    def update_old_data_sql(self, table_name, dict1, dict2):
        set_string = self.concat(dict1, ",")
        where_string = self.concat(dict2, " AND ")
        sql = "UPDATE %s SET %s WHERE %s" % (table_name, set_string, where_string)
        return sql

    def delete_data_sql(self, table_name, **kwargs):
        where_string = self.concat(kwargs, ' AND ')
        sql = "delete from %s where %s" % (table_name, where_string)
        return sql

    def select(self, sql):
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        return res

    def select_dict(self, sql):
        self.cursor_dict.execute(sql)
        res = self.cursor_dict.fetchall()
        return res

    # 批量插入数据
    def bulk_insert(self, table_name, *args):
        keys = ",".join(args[0])
        value_list = []
        for get_dict in args:
            temp = []
            for k, v in get_dict.items():
                temp.append("'" + str(v) + "'")
            string = "(" + ",".join(temp) + ")"
            value_list.append(string)
        values = ",".join(value_list)
        sql = "INSERT INTO %s (%s) VALUES %s" % (table_name, keys, values)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.con.rollback()
            print(e)
        else:
            self.con.commit()


def connection(**kwargs):
    if kwargs:
        db_settings = kwargs
    else:
        db_settings = SQL_SETTINGS
    while True:
        try:
            con = pymysql.connect(**db_settings)
        except OperationalError as e:
            logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
            sleep(5)
        else:
            break
    cursor = con.cursor()
    cursor_dict = con.cursor(cursor=pymysql.cursors.DictCursor)
    return con, cursor, cursor_dict


def get_data(**kwargs):
    try:
        type(kwargs["help"])
        return """get_data()帮助文档：
    :参数 help: 输出帮助文档
    :参数 sql: 直接使用传入的sql语句
    :参数 t: 需要查询的表名，字符串
    :参数 l: 查询输出结果的条数，整数类型
    :参数 o: 对结果集进行排序，列表类型
    :参数 om: 排序的方式，默认是升序，默认值 a ,可选值 d
    :参数 g: 根据一个或多个列对结果集进行分组，列表类型
    :参数 db: 数据库连接配置，字典类型
    :参数 cn: 输出结果集的列名，列表类型
    :参数 c: 查询条件,字典类型
    :参数 only_sql: 布尔类型，不返回查询结果只返回函数转化的sql语句，默认为False
    :参数 dict_result: 布尔类型，将返回字典类型的查询结果，默认为False
    :参数 return_one: 布尔类型，只返回第一个值，如果没有返回空
    :返回值: 返回元组类型的查询结果"""
    except KeyError:
        pass

    try:
        assert type(kwargs["t"]) is str and kwargs["t"] is not None, "t的数据类型必需是字符串,并且不能为空"
        table_name = kwargs["t"]
    except KeyError:
        pass

    try:
        assert type(kwargs["l"]) is int, "l的数据类型必需是整形(int)"
        limit_str = " limit " + str(kwargs["l"])
    except KeyError:
        limit_str = " limit 100"

    try:
        assert type(kwargs["o"]) is list, "o的数据类型必需是列表"
        order_by_str = " order by " + ",".join(kwargs["o"])
        try:
            assert kwargs["om"] == "d" or kwargs["om"] == "a", "om的参数值必需是d或a，默认值a"
            if kwargs["om"] == "a":
                order_by_str += " " + "asc"
            elif kwargs["om"] == "d":
                order_by_str += " " + "desc"
        except KeyError:
            order_by_str += " " + "asc"
    except KeyError:
        order_by_str = ""

    try:
        assert type(kwargs["g"]) is list, "o的数据类型必需是列表"
        group_by_str = " group by " + ",".join(kwargs["g"])
    except KeyError:
        group_by_str = ""

    try:
        assert type(kwargs["cn"]) is list, "cn的数据类型必需是列表"
        column_name_str = ",".join(kwargs["cn"])
    except KeyError:
        column_name_str = "*"

    try:
        assert type(kwargs["c"]) is dict, "sc的数据类型必需是字典(dict)"
        condition = " where " + concat(kwargs["c"], "and ")
    except KeyError:
        condition = ""

    try:
        assert type(kwargs['sql']) is str, "sql的数据类型必需是字典(str)"
        sql = kwargs['sql']
    except KeyError:
        sql = "select %s from %s%s%s%s%s" % (
            column_name_str, table_name, condition, group_by_str, order_by_str, limit_str)

    try:
        assert type(kwargs["db"]) is dict, "db的数据类型必需是字典(dict)"
        db = kwargs["db"]
    except KeyError:
        db = {}

    try:
        assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
        if kwargs["only_sql"]:
            print(sql)
            return None
    except KeyError:
        pass

    con, cursor, cursor_dict = connection(**db)

    try:
        assert type(kwargs["dict_result"]) is bool, "dict_result的数据类型必需是bool类型"
        if kwargs["dict_result"]:
            while True:
                try:
                    con.ping(reconnect=True)
                    cursor_dict.execute(sql)
                except OperationalError as e:
                    logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                    sleep(5)
                except Error as e:
                    logger.error("异常报错的sql语句：" + sql)
                    logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                    return None
                else:
                    result = cursor_dict.fetchall()
                    con.close()
                    break
        else:
            while True:
                try:
                    con.ping(reconnect=True)
                    cursor.execute(sql)
                except OperationalError as e:
                    logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                    sleep(5)
                except Error as e:
                    logger.error("异常报错的sql语句：" + sql)
                    logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                    return None
                else:
                    result = cursor.fetchall()
                    con.close()
                    break
    except KeyError:
        while True:
            try:
                con.ping(reconnect=True)
                cursor.execute(sql)
            except OperationalError as e:
                logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                sleep(5)
            except Error as e:
                logger.error("异常报错的sql语句：" + sql)
                logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                return None
            else:
                result = cursor.fetchall()
                con.close()
                break
    try:
        assert type(kwargs["return_one"]) is bool, "return_one的数据类型必需是bool类型"
        if kwargs['return_one']:
            if result:
                return result[0][0]
            else:
                return None
        else:
            return result
    except KeyError:
        return result


def update_data(**kwargs):
    try:
        type(kwargs["help"])
        print("""update_data()帮助文档：
    :参数 help: 输出帮助文档
    :参数 sql: 直接使用传入的sql语句
    :参数 t: 需要更新的表名，字符串
    :参数 set: 需要更新的表头与数值，字典类型
    :参数 db: 数据库连接配置，字典类型
    :参数 c: 执行更新的条件,字典类型
    :参数 only_sql: 布尔类型，不返回查询结果只返回函数转化的sql语句，默认为False
    :返回值: 返回元组类型的查询结果""")
        return None
    except KeyError:
        pass

    try:
        assert type(kwargs["t"]) is str and kwargs["t"] is not None, "t的数据类型必需是字符串,并且不能为空"
        table_name = kwargs["t"]
    except KeyError:
        pass

    try:
        assert type(kwargs['set']) is dict, "set的数据类型必需是字典(dict)"
        set_str = concat(kwargs['set'], ",")
    except KeyError:
        pass

    try:
        assert type(kwargs["c"]) is dict, "c的数据类型必需是字典"
        condition = concat(kwargs['c'], " and ")
    except KeyError:
        pass

    try:
        assert type(kwargs["sql"]) is str, "sql的数据类型必需是字符串"
        sql = kwargs["sql"]
    except KeyError:
        sql = "update %s set %s where %s" % (table_name, set_str, condition)

    try:
        assert type(kwargs["db"]) is dict, "db的数据类型必需是字典(dict)"
        db = kwargs["db"]
    except KeyError:
        db = {}

    try:
        assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
        if kwargs["only_sql"]:
            print(sql)
            return None
    except KeyError:
        pass

    con, cursor, cursor_dict = connection(**db)
    while True:
        try:
            con.ping(reconnect=True)
            cursor.execute(sql)
        except OperationalError as e:
            logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
            sleep(5)
        except Error as e:
            logger.error("异常报错的sql语句：" + sql)
            logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
            con.rollback()
            con.close()
            break
        else:
            con.commit()
            con.close()
            break


def insert_data(**kwargs):
    try:
        type(kwargs["help"])
        print("""insert_data()帮助文档：
    :参数 help: 输出帮助文档
    :参数 sql: 直接使用传入的sql语句
    :参数 t: 需要写入的表名，字符串
    :参数 d: 需要写入的数据，字典类型
    :参数 db: 数据库连接配置，字典类型
    :参数 only_sql: 布尔类型，不返回查询结果只返回函数转化的sql语句，默认为False
    :返回值: 返回元组类型的查询结果""")
        return None
    except KeyError:
        pass

    try:
        assert type(kwargs["t"]) is str and kwargs["t"] is not None, "t的数据类型必需是字符串,并且不能为空"
        table_name = kwargs["t"]
    except KeyError:
        pass

    try:
        assert type(kwargs["d"]) is dict, "d的数据类型必需是字典类型"
        keys = ",".join(kwargs["d"].keys())
        x = []
        for k, v in kwargs["d"].items():
            x.append(str(v))
        values = "'" + "','".join(x) + "'"
    except KeyError:
        pass

    try:
        assert type(kwargs["sql"]) is str, "sql的数据类型必需是字符串"
        sql = kwargs["sql"]
    except KeyError:
        sql = "insert into %s(%s) values(%s)" % (table_name, keys, values)

    try:
        assert type(kwargs["db"]) is dict, "db的数据类型必需是字典(dict)"
        db = kwargs["db"]
    except KeyError:
        db = {}

    try:
        assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
        if kwargs["only_sql"]:
            print(sql)
            return None
    except KeyError:
        pass

    con, cursor, cursor_dict = connection(**db)

    while True:
        try:
            con.ping(reconnect=True)
            cursor.execute(sql)
        except OperationalError as e:
            logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
            sleep(5)
        except Error as e:
            logger.error("异常报错的sql语句：" + sql)
            logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
            con.rollback()
            con.close()
            break
        else:
            con.commit()
            con.close()
            break


def delete_data(**kwargs):
    try:
        type(kwargs["help"])
        print("""delete_data()帮助文档：
    :参数 help: 输出帮助文档
    :参数 sql: 直接使用传入的sql语句
    :参数 t: 需要删除数据的表名，字符串
    :参数 c: 删除数据的条件，字典类型
    :参数 db: 数据库连接配置，字典类型
    :参数 only_sql: 布尔类型，不返回查询结果只返回函数转化的sql语句，默认为False
    :返回值: 返回元组类型的查询结果""")
        return None
    except KeyError:
        pass

    try:
        assert type(kwargs["t"]) is str and kwargs["t"] is not None, "t的数据类型必需是字符串,并且不能为空"
        table_name = kwargs["t"]
    except KeyError:
        pass

    try:
        assert type(kwargs["c"]) is dict, "c的数据类型必需是字典"
        condition = concat(kwargs['c'], " and ")
    except KeyError:
        pass

    try:
        assert type(kwargs["sql"]) is str, "sql的数据类型必需是字符串"
        sql = kwargs["sql"]
    except KeyError:
        sql = "delete from %s where %s" % (table_name, condition)

    try:
        assert type(kwargs["db"]) is dict, "db的数据类型必需是字典(dict)"
        db = kwargs["db"]
    except KeyError:
        db = {}

    try:
        assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
        if kwargs["only_sql"]:
            print(sql)
            return None
    except KeyError:
        pass

    con, cursor, cursor_dict = connection(**db)

    while True:
        try:
            con.ping(reconnect=True)
            cursor.execute(sql)
        except OperationalError as e:
            logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
            sleep(5)
        except Error as e:
            logger.error("异常报错的sql语句：" + sql)
            logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
            con.rollback()
            con.close()
            break
        else:
            con.commit()
            con.close()
            break


def concat(dictionary, string):
    """
    拼装字典
    :param dictionary: 需要拼装的字典
    :param string: 拼装时所使用的连接的字符
    :return: key='value' string key='value' string key='value'...
    """
    for k, v in dictionary.items():
        dictionary[k] = str(v)
    list_key_value = []
    for k, v in dictionary.items():
        list_key_value.append(k + "=" + "\'" + v + "\'")
    conditions = string.join(list_key_value)
    return conditions


if __name__ == '__main__':
    db = {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '', 'db': 'demo', }
    res = get_data(t="tb_order_detail_spider", c={"orderNo": "641471107794514866"},
                   dict_result=True)
    print(res)
