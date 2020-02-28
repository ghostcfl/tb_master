import asyncio
import mysql
import re
from settings import MY_TB_ACCOUNT, test_server
from pyquery import PyQuery as pq

test_server['db'] = 'test'


class MasterSpider(object):
    start_url = 'https://szsaibao.taobao.com/search.htm?search=y&orderType=hotsell_desc&pageNo='
    view_prot = {"width": 1600, "height": 900}
    total_page_num = 0

    def __init__(self, b, p):
        self.browser = b
        self.page = p

    def __del__(self):
        # self.loop.run_until_complete(self.browser.close())
        # self.loop.close()
        pass

    async def get_html(self, page_control, speed=1):
        page_num = 1
        while page_num <= page_control:
            await self.page.goto(self.start_url + str(page_num))
            await self.page.waitForSelector(".item4line1")
            page_num += 1
            yield await self.page.content()
            if self.total_page_num and page_num > self.total_page_num:
                break
            await asyncio.sleep(speed)

    async def parse(self):
        item = {}
        async for html in self.get_html(1000, speed=10):
            doc = pq(html)
            if not self.total_page_num:
                num = doc(".pagination span.page-info").text()
                self.total_page_num = int(re.findall("/(\d+)", num)[0])
            items = doc(".item4line1 dl.item").items()
            for i in items:
                item['typeabbrev'] = "TB"
                item['shop_id'] = "34933991"
                item['link_id'] = i.attr("data-id")
                item['description'] = i.find("dd.detail a").text()
                if i.find("div.cprice-area span.c-price").text():
                    item['cprice'] = float(i.find("div.cprice-area span.c-price").text())
                else:
                    item['cprice'] = 0
                if i.find("div.sprice-area span.s-price").text():
                    item['sprice'] = float(i.find("div.sprice-area span.s-price").text())
                else:
                    item['sprice'] = 0
                if i.find("div.sale-area span.sale-num").text():
                    item['sale_num'] = int(i.find("div.sale-area span.sale-num").text())
                else:
                    item['sale_num'] = 0
                yield item

    async def save(self):
        async for i in self.parse():
            res = mysql.get_data(db=test_server, t="tb_master", cn=['cprice', 'sprice', 'sale_num'],
                                 c={'link_id': i['link_id']}, dict_result=True)
            if res:
                if res[0]['cprice'] != i['cprice']:
                    mysql.update_data(db=test_server, t="tb_master", set={"cprice": i['cprice']},
                                      c={'link_id': i['link_id']})
                    print("更新销售价")
                if res[0]['sprice'] != i['sprice']:
                    mysql.update_data(db=test_server, t="tb_master", set={"sprice": i['sprice']},
                                      c={'link_id': i['link_id']})
                    print("更新原价")
                if res[0]['sale_num'] != i['sale_num']:
                    mysql.update_data(db=test_server, t="tb_master", set={"sprice": i['sprice']},
                                      c={'link_id': i['link_id']})
                    print("更新销量")
            else:
                mysql.insert_data(db=test_server, t="tb_master", d=i)


from Login_New import Login

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    l = Login()
    b, p = loop.run_until_complete(l.login(**MY_TB_ACCOUNT))
    master = MasterSpider(b, p)
    loop.run_until_complete(master.save())
