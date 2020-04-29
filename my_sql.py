import pymysql
from pymysql.err import OperationalError
from Format import sleep as my_sleep

from settings import MAIN_SQL_SETTING
from logger import get_logger

logger = get_logger()


class MySql(object):
    _cursor = None
    _dict_cursor = None
    _con = None

    def __init__(self, db_setting=None):
        # logger.info("打开数据库连接")
        db_setting = db_setting if db_setting else MAIN_SQL_SETTING
        while 1:
            try:
                self._con = pymysql.connect(**db_setting)
            except OperationalError as e:
                logger.error("数据库链接异常，1分钟后尝试重连，原因：" + str(e))
                my_sleep()
            else:
                self._cursor = self._con.cursor()
                self._dict_cursor = self._con.cursor(cursor=pymysql.cursors.DictCursor)
                break

    def __del__(self):
        # logger.info("关闭数据库连接")
        self._cursor.close()
        self._dict_cursor.close()
        self._con.close()

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
            list_key_value.append(k + "=" + "\'" + v + "\'")
        conditions = string.join(list_key_value)
        return conditions

    def get(self, **kwargs):
        try:
            type(kwargs["help"])
            print("""get_data()帮助文档：
            :参数 help: 输出帮助文档
            :参数 sql: 直接使用传入的sql语句
            :参数 t: 需要查询的表名，字符串
            :参数 l: 查询输出结果的条数，list类型[start,limit]
            :参数 o: 对结果集进行排序，列表类型
            :参数 om: 排序的方式，默认是升序，默认值 a ,可选值 d
            :参数 g: 根据一个或多个列对结果集进行分组，列表类型
            :参数 cn: 输出结果集的列名，列表类型
            :参数 c: 查询条件,字典类型
            :参数 only_sql: 布尔类型，不返回查询结果只返回函数转化的sql语句，默认为False
            :参数 dict_result: 布尔类型，将返回字典类型的查询结果，默认为False
            :参数 return_one: 布尔类型，只返回第一个值，如果没有返回空
            :返回值: 返回元组类型的查询结果""")
        except KeyError:
            pass

        try:
            assert type(kwargs["t"]) is str and kwargs["t"] is not None, "t的数据类型必需是字符串,并且不能为空"
            table_name = kwargs["t"]
        except KeyError:
            pass

        try:
            assert type(kwargs["l"]) is list, "l的数据类型必需是整形(list)"
            limit_str = " limit " + ",".join(kwargs["l"])
        except KeyError:
            limit_str = " limit 0,1000"

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
            condition = " where " + self.concat(kwargs["c"], "and ")
        except KeyError:
            condition = ""

        try:
            assert type(kwargs['sql']) is str, "sql的数据类型必需是字典(str)"
            sql = kwargs['sql']
        except KeyError:
            sql = "select %s from %s%s%s%s%s" % (
                column_name_str, table_name, condition, group_by_str, order_by_str, limit_str)

        try:
            assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
            if kwargs["only_sql"]:
                print(sql)
                return None
        except KeyError:
            pass

        try:
            assert type(kwargs["dict_result"]) is bool, "dict_result的数据类型必需是bool类型"
            if kwargs["dict_result"]:
                while True:
                    try:
                        self._con.ping(reconnect=True)
                        self._dict_cursor.execute(sql)
                    except OperationalError as e:
                        logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                        my_sleep(5)
                    except Exception as e:
                        logger.error("异常报错的sql语句：" + sql)
                        logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                        return None
                    else:
                        result = self._dict_cursor.fetchall()
                        self._con.commit()
                        break
            else:
                while True:
                    try:
                        self._con.ping(reconnect=True)
                        self._cursor.execute(sql)
                    except OperationalError as e:
                        logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                        my_sleep(5)
                    except Exception as e:
                        logger.error("异常报错的sql语句：" + sql)
                        logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                        return None
                    else:
                        result = self._con.fetchall()
                        self._con.commit()
                        break
        except KeyError:
            while True:
                try:
                    self._con.ping(reconnect=True)
                    self._cursor.execute(sql)
                except OperationalError as e:
                    logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                    my_sleep(5)
                except Exception as e:
                    logger.error("异常报错的sql语句：" + sql)
                    logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                    return None
                else:
                    result = self._cursor.fetchall()
                    self._con.commit()
                    break
        try:
            assert type(kwargs["return_one"]) is bool, "return_one的数据类型必需是bool类型"
            if kwargs['return_one']:
                return result[0][0] if result else None
            else:
                return result
        except KeyError:
            return result

    @classmethod
    def cls_get(cls, db_setting=None, **kwargs):
        ms = MySql(db_setting=db_setting)
        result = ms.get(**kwargs)
        del ms
        return result

    def get_one(self, **kwargs):
        return self.get(return_one=True, **kwargs)

    @classmethod
    def cls_get_one(cls, db_setting=None, **kwargs):
        ms = MySql(db_setting=db_setting)
        result = ms.get_one(**kwargs)
        del ms
        return result

    def get_dict(self, **kwargs):
        return self.get(dict_result=True, **kwargs)

    @classmethod
    def cls_get_dict(cls, db_setting=None, **kwargs):
        ms = MySql(db_setting=db_setting)
        result = ms.get_dict(**kwargs)
        del ms
        return result

    def print_get_sql(self, **kwargs):
        self.get(only_sql=True, **kwargs)

    def print_get_help(self, **kwargs):
        print(self.get(help=True, **kwargs))

    def update(self, **kwargs):
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
            set_str = self.concat(kwargs['set'], ",")
        except KeyError:
            pass

        try:
            assert type(kwargs["c"]) is dict, "c的数据类型必需是字典"
            condition = self.concat(kwargs['c'], " and ")
        except KeyError:
            pass

        try:
            assert type(kwargs["sql"]) is str, "sql的数据类型必需是字符串"
            sql = kwargs["sql"]
        except KeyError:
            sql = "update %s set %s where %s" % (table_name, set_str, condition)

        try:
            assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
            if kwargs["only_sql"]:
                print(sql)
                return None
        except KeyError:
            pass

        while True:
            try:
                self._con.ping(reconnect=True)
                self._cursor.execute(sql)
            except OperationalError as e:
                logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                my_sleep(5)
            except Exception as e:
                logger.error("异常报错的sql语句：" + sql)
                logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                self._con.rollback()
                break
            else:
                self._con.ping(reconnect=True)
                self._con.commit()
                break

    @classmethod
    def cls_update(cls, db_setting=None, **kwargs):
        ms = MySql(db_setting=db_setting)
        ms.update(**kwargs)
        del ms

    def print_update_help(self, **kwargs):
        self.update(help=True, **kwargs)

    def print_update_sql(self, **kwargs):
        self.update(only_sql=True, **kwargs)

    def insert(self, **kwargs):
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
            assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
            if kwargs["only_sql"]:
                print(sql)
                return None
        except KeyError:
            pass

        while True:
            try:
                self._con.ping(reconnect=True)
                self._cursor.execute(sql)
            except OperationalError as e:
                logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                my_sleep(5)
            except Exception as e:
                logger.error("异常报错的sql语句：" + sql)
                logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                self._con.rollback()
                break
            else:
                self._con.commit()
                break

    @classmethod
    def cls_insert(cls, db_setting=None, **kwargs):
        ms = MySql(db_setting=db_setting)
        ms.insert(**kwargs)
        del ms

    def print_insert_help(self, **kwargs):
        self.insert(help=True, **kwargs)

    def print_insert_sql(self, **kwargs):
        self.insert(only_sql=True, **kwargs)

    def delete(self, **kwargs):
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
            condition = self.concat(kwargs['c'], " and ")
        except KeyError:
            pass

        try:
            assert type(kwargs["sql"]) is str, "sql的数据类型必需是字符串"
            sql = kwargs["sql"]
        except KeyError:
            sql = "delete from %s where %s" % (table_name, condition)

        try:
            assert type(kwargs["only_sql"]) is bool, "only_sql的数据类型必需是bool类型"
            if kwargs["only_sql"]:
                print(sql)
                return None
        except KeyError:
            pass

        while True:
            try:
                self._con.ping(reconnect=True)
                self._cursor.execute(sql)
            except OperationalError as e:
                logger.error("数据库链接异常，5秒后尝试重连，原因：" + str(e))
                my_sleep(5)
            except Exception as e:
                logger.error("异常报错的sql语句：" + sql)
                logger.error("异常内容：" + str(e) + "|异常类型：" + str(type(e)))
                self._con.rollback()
                break
            else:
                self._con.commit()
                break

    def print_delete_help(self, **kwargs):
        self.delete(help=True, **kwargs)

    def print_delete_sql(self, **kwargs):
        self.delete(only_sql=True, **kwargs)


if __name__ == '__main__':
    res = MySql.cls_get_dict(t="tb_order_spider",
                             cn=["detailURL", "orderNo"],
                             c={"isDetaildown": 0, "fromStore": "KY"},
                             o=["createTime"], om="d")
    print(res)
    pass
    # from settings import TEST_SERVER_DB_TEST
    #
    # ms = MySql(db_setting=TEST_SERVER_DB_TEST)
    # while 1:
    #     my_sleep(5)
    #     verify_code = ms.get_one(sql="select verify_code from phone_verify where id='59' limit 1000")
    #     print(verify_code)
    # ms.print_get_help(t="shop_info")
    # print()
