import mysql
import re
import requests
import Format
from requests import Session
from settings import test_server, MY_TB_ACCOUNT
from request_headers import get_request_headers
from Login_New import Login

test_server['db'] = "test"


class Slaver(object):
    url = "https://item.taobao.com/item.htm?id="
    # proxy_url = "http://http.tiqu.alicdns.com/getip3?num=1&type=1&pro=&city=0&yys=0&port=11&pack=37356&ts=0&ys=0&cs=1&lb=1&sb=0&pb=45&mr=1&regions=110000,130000,140000,150000,210000,230000,310000,320000,330000,340000,350000,360000,370000,410000,420000,430000,440000,500000,510000,530000,610000,640000&gm=4"
    proxy_url = "http://http.tiqu.alicdns.com/getip3?num=1&type=1&pro=&city=0&yys=0&port=11&pack=90994&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=&gm=4"
    proxies = None

    def __init__(self):
        pass

    def _set_proxy(self):
        r = requests.get(self.proxy_url)
        proxy = re.sub("\s+", "", r.text)  # 获得代理IP
        Format._write("2", "proxy", proxy)
        return

    @staticmethod
    def _get_item():
        sql = "SELECT shop_id,link_id,description,price,promotionPrice,sale_num FROM tb_master WHERE isUsed=0 and link_id='{}' LIMIT 1".format(
            "586886697621")
        while 1:
            result = mysql.get_data(db=test_server, sql=sql, dict_result=True)
            if result:
                yield result[0]
            else:
                break

    def _get_html(self):
        count = 0
        session = Session()
        for item in self._get_item():
            # url = self.url + item['link_id']
            url = self.url + "586886697621"
            try:
                proxy = Format._read("2", "proxy")
                print(proxy)
                if not proxy:
                    self._set_proxy()
                proxies = {"https": "https://{}".format(proxy)}
                r = session.get(url=url, headers=get_request_headers(), proxies=proxies, timeout=10)
                print(r.status_code, end="1111")
                print()
                count += 1
            except requests.exceptions.ProxyError:
                # self._set_proxy()
                try:
                    r = session.get(url="https://httpbin.org/get", headers=get_request_headers(), proxies=proxies)
                except requests.exceptions.ProxyError:
                    print("x")
                    self._set_proxy()
                    # count += 1
                    # print(r.status_code, end="2")
                    # print(r.json())
                # session = requests.Session()
            except Exception as e:
                print(e)
            # print(r.status_code, end="1")
            else:
                yield r.text, item

    def parse(self):
        for html, item in self._get_html():
            pass
            # a = re.findall('";(.*?);".*?e":"(\d+\.\d+).*?skuId":"(\d+)', html)
            # if a:
            #     discount = 0
            #     if float(item['promotionPrice']) > 0:
            #         discount = round(float(item['price']) - float(item['promotionPrice']), 4)
            #     print(discount)
            #     for i in range(len(a)):
            #         item['price'] = float(a[i][1])
            #         item['skuId'] = a[i][2]
            #         if discount:
            #             item['promotionPrice'] = round(item['price'] - discount, 4)
            #         print(item)
            # input()

    @classmethod
    def run(cls):
        s = Slaver()
        s.parse()


# res = requests.get("https://item.taobao.com/item.htm?id=%s" % (str(link_id)))
if __name__ == '__main__':
    Slaver.run()
