import re, datetime, time, subprocess, asyncio, requests, shelve, os
from logger import get_logger
from settings import LINUX

logger = get_logger()


def time_now_str():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def date_now_str():
    return datetime.datetime.now().strftime('%Y%m%d')


def yesterday(time):
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    return str(yesterday) + " " + time


def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def time_stamp():
    return str(int(time.time()))


def time_zone(args):
    time_list = []
    for t in args:
        d_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + t, '%Y-%m-%d%H:%M')
        time_list.append(d_time)
    return time_list


def status_format(string):
    list = ["等待买家付款", "买家已付款", "交易关闭", "已发货", "交易成功"]
    for i in list:
        a = re.search(i, string)
        if a:
            if a.group() == "已发货":
                temp = "卖家已发货"
            else:
                temp = a.group()
            return temp


def delivery_company_translate(company_name):
    if company_name == "韵达快递":
        ship_via = "2"
    elif company_name == "圆通快递":
        ship_via = "3"
    elif company_name == "申通快递":
        ship_via = "4"
    elif company_name == "顺丰快递":
        ship_via = "5"
    elif company_name == "优速快递":
        ship_via = "6"
    elif company_name == "中通快递":
        ship_via = "7"
    else:
        ship_via = "1"
    return ship_via


def store_trans(string):
    if string == "YK":
        return '玉佳企业店'
    elif string == "KY":
        return "开源电子"
    elif string == "SC":
        return '微信商城'
    elif string == "VP":
        return '批发'
    elif string == "YJ":
        return "玉佳电子"
    elif string == "TB":
        return "赛宝电子"


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
        list_key_value.append(k + "=" + '\'' + v + '\'')
    conditions = string.join(list_key_value)
    return conditions


def sleep(x=60):
    assert type(x) is int and x > 0, "x的类型必需为整形并大于0"
    time.sleep(1)
    print(time_now() + " | ", end="", flush=True)
    for i in range(x):
        time.sleep(1)
        print(">", end="", flush=True)
    print("")
    time.sleep(1)


async def async_sleep(x=60):
    assert type(x) is int and x > 0, "x的类型必需为整形并大于0"
    await asyncio.sleep(1)
    print(time_now() + " | ", end="", flush=True)
    for i in range(x):
        await asyncio.sleep(1)
        print(">", end="", flush=True)
    print("")
    await asyncio.sleep(1)


def ping_net_check(url):
    if LINUX:
        cmd = "ping -c 4 " + url
        a = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = a.returncode
    else:
        cmd = "ping " + url
        res = subprocess.call(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res


def net_check(url=None):
    if not url:
        url = "www.baidu.com"
    while True:
        if not ping_net_check(url):
            break
        logger.info("当前网络异常，1分钟后尝试重连")
        sleep(60)
    return


def write(*args, **kwargs):
    if not os.path.exists("data"):
        os.mkdir("data")

    with shelve.open("data/data") as db:
        for i in range(len(args)):
            db['t' + str(i)] = args[i]


def read():
    with shelve.open("data/data") as db:
        for i in db:
            yield i, db[i]


if __name__ == '__main__':
    print(yesterday("18:00:00"))

