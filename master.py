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
    def format_request_params(curl):
        curl = re.sub("\"", "", curl)
        a = curl.split(" -H ")
        params = {}
        cookies = {}
        headers = {}
        for b in a:
            if re.match("curl", b):
                c = b.split(" ")[-1]
                url = c.split("?", 1)[0]
                d = c.split("?", 1)[1].split("&")
                for e in d:
                    f = e.split("=", 1)
                    params[f[0]] = f[1]
            elif re.match("Cookie", b):
                g = b.split(": ")[-1]
                h = g.split("; ")
                for i in h:
                    j = i.split("=", 1)
                    cookies[j[0]] = j[1]
            else:
                k = b.split(": ", 1)
                headers[k[0]] = k[1]
        return url, params, cookies, headers

    @staticmethod
    def _get_shop_id():
        sql = "select shop_id from shop_info where shop_id!='88888888'"  # 获取所有的店铺ID
        shop_infos = mysql.get_data(sql=sql, dict_result=True)
        for shop_info in shop_infos:
            if shop_info['shop_id'] == "115443253":
                yield shop_info['shop_id']

    def _get_html(self):
        for shop_id in self._get_shop_id():
            pass

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
            try:
                match = re.search("item\dline1", html).group()
            except Exception as e:
                logger.error(e)
                with open("error.html", 'w') as f:
                    f.write(html)
                logger.error("未知错误导致程序退出查看error.html文件")
                exit(0)
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
