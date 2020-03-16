import requests
import mysql
import time
import re
import Format
import random
from settings import test_server
from pyquery import PyQuery
from datetime import date
from logger import get_logger
from reports import Reports

test_server['db'] = 'test'
logger = get_logger()


class Master(object):
    @staticmethod
    def _get_headers(result):
        headers = {
            "Accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Connection": "keep-alive",
            "Cookie": result['cookies'],
            "Host": "shop" + result['shop_id'] + ".taobao.com",
            "Referer": result['refer'],
            "TE": "Trailers",
            "User-Agent": result['user_agent'],
            "X-Requested-With": "XMLHttpRequest",
        }
        return headers

    @staticmethod
    def _get_url(result, page_num):
        time_str = str(int(time.time() * 1000))
        url = "https://szsaibao.taobao.com/i/asynSearch.htm?"
        get_data = {
            "_ksTS": time_str + "_" + result["_ksTS"],
            "callback": result['callback'],
            "mid": result['mid'],
            "wid": result['wid'],
            "path": "/search.htm",
            "search": "y",
            "spm": result['spm'],
            "input_charset": "gbk",
            "orderType": "hotsell_desc",
            "pageNo": str(page_num)
        }
        data_str_list = []
        for k, v in get_data.items():
            data_str_list.append(k + "=" + v)
        data_str = "&".join(data_str_list)
        url += data_str
        return url

    @staticmethod
    def _get_shop_id():
        sql = "select shop_id from shop_info where shop_id!='88888888'"  # 获取所有的店铺ID
        shop_infos = mysql.get_data(sql=sql, dict_result=True)
        for shop_info in shop_infos:
            if shop_info['shop_id'] == "115443253":
                yield shop_info['shop_id']

    def _get_html(self):
        shop_ids = []
        for shop_id in self._get_shop_id():
            page_control = Format._read(shop_id=shop_id, flag="total_page")  # 获得存储在本地的店铺总的页码数量
            if not page_control:
                page_control = 1000  # 如果没有获取到页码总数，给个1000的总数
            shop_ids.append(shop_id)  # 将店铺ID存储起来用于后面重置翻页数据
            page_num = Format._read(shop_id=shop_id, flag="page_num")  # 读取存储在本地的page_num
            while page_num < page_control:
                start_time = time.time()  # 本页面开始的时间存入变量
                result = mysql.get_data(db=test_server, t='user_record', c={"shop_id": shop_id}, l=1, dict_result=True)
                headers = self._get_headers(result[0])
                url = self._get_url(result[0], page_num + 1)
                r = requests.get(url=url, headers=headers)
                html = r.text.replace("\\", "")
                html = re.sub("jsonp\d+\(\"|\"\)", "", html)
                yield html, shop_id

                Format._write(shop_id=shop_id, flag="page_num", value=page_num + 1)  # 将下次需要爬取的页码存入本地的配件中
                page_num = Format._read(shop_id, "page_num")  # 读取下一次要爬取的页码
                page_control = Format._read(shop_id=shop_id, flag="total_page")  # 获得存储在本地的店铺总的页码数量
                s = random.randrange(20, 50) * random.random()
                logger.info("休息{}秒，开始爬取下一页".format(s))
                time.sleep(s)
                spent_time_this_page = time.time() - start_time  # 计算本页完成时间
                spent_time = Format._read(shop_id=shop_id, flag="spent_time")  # 读取上一次存储在本地的时间
                Format._write(shop_id=shop_id, flag="spent_time",
                              value=spent_time + spent_time_this_page)  # 将本页面完成时间加上后并存储在本地
            is_mail = Format._read(shop_id, "mail")
            if not is_mail:
                Reports().report(shop_id.split(" "))
        for shop_id in shop_ids:
            Format._del(shop_id=shop_id, flag="page_num")  # 重置翻页的数据
            Format._del(shop_id=shop_id, flag="total_page")  # 重置总页码数据
            Format._del(shop_id=shop_id, flag="mail")  # 重置邮件标记
            Format._del(shop_id=shop_id, flag="spent_time")  # 重置完成时间

    def _parse(self):
        for html, shop_id in self._get_html():
            verify = re.search("login\.taobao\.com", html)
            if verify:
                with open("error.html", 'w') as f:
                    f.write(html)
                logger.error("response返回结果错误，无法解析，请使用user_record重新获取登陆的COOKIES")
                exit(0)

            doc = PyQuery(html)
            #  存在未知错误的时候，写错误的HTML写到文件中
            match = re.search("item\dline1", html).group()
            if not match:
                with open("error.html", 'w') as f:
                    f.write(html)
                logger.error("未知错误导致程序退出查看error.html文件")
                exit(0)

            total_page = Format._read(shop_id=shop_id, flag="total_page")
            if not total_page:
                num = doc(".pagination span.page-info").text()
                Format._write(shop_id=shop_id, flag="total_page", value=int(re.findall("/(\d+)", num)[0]))

            items = doc("." + match + " dl.item").items()
            for i in items:
                item = {}
                item['shop_id'] = shop_id
                item['link_id'] = i.attr('data-id')
                item['description'] = i.find("dd.detail a").text()
                item['update_date'] = date.today()
                item['flag'] = "insert"
                cprice = float(i.find("div.cprice-area span.c-price").text())
                if i.find("div.sprice-area span.s-price").text():
                    sprice = float(i.find("div.sprice-area span.s-price").text())
                else:
                    sprice = 0
                if i.find("div.sale-area span.sale-num").text():
                    item['sale_num'] = int(i.find("div.sale-area span.sale-num").text())
                else:
                    item['sale_num'] = 0
                if sprice:
                    item['price'] = sprice
                    item['promotionPrice'] = cprice
                else:
                    item['price'] = cprice
                    item['promotionPrice'] = sprice
                yield item

    def save(self):
        for i in self._parse():
            print(i)
            res = mysql.get_data(db=test_server, t="tb_master",
                                 c={'link_id': i['link_id']}, dict_result=True)
            flag = ["update"]
            narrative = []
            if res:
                if res[0]['price'] != i['price']:
                    flag.append("price")
                    narrative.append("更新销售价格:[{}]=>[{}]".format(res[0]['price'], i['price']))
                if res[0]['promotionPrice'] != i['promotionPrice']:
                    flag.append("promotion")
                    narrative.append("更新优惠售价格:[{}]=>[{}]".format(res[0]['promotionPrice'], i['promotionPrice']))
                if res[0]['sale_num'] != i['sale_num']:
                    flag.append("sale")
                    narrative.append("更新销量:[{}]=>[{}]".format(res[0]['sale_num'], i['sale_num']))
                i['flag'] = "_".join(flag)
                i['narrative'] = ";".join(narrative)
                mysql.update_data(db=test_server, t='tb_master', set=i, c={"link_id": i['link_id']})
            else:
                i['flag'] = 'insert'
                mysql.insert_data(db=test_server, t="tb_master", d=i)


if __name__ == '__main__':
    m = Master()
    m.save()
