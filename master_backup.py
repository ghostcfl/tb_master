import asyncio
import mysql
import re
import Format
import time
from settings import MY_TB_ACCOUNT, test_server, dev
from pyppeteer import launch, errors
from datetime import date
from pyquery import PyQuery as pq
from Login_New import Login
from reports import Reports

test_server['db'] = 'test'


class MasterSpider(object):
    start_url = 'https://shop.taobao.com/'
    view_prot = {"width": 1600, "height": 900}

    def __init__(self, b, p, l):
        self.browser = b
        self.page = p
        self.login = l
        pass

    async def _jump_to_search_page(self):
        await self.page.waitForSelector(".all-cats-trigger.popup-trigger")
        await self.page.click(".all-cats-trigger.popup-trigger")

    async def _goto_last_page_num(self, page_num):
        print(page_num)
        await self.page.waitForSelector('.pagination input[name="pageNo"]')
        await self.page.click('.pagination input[name="pageNo"]', clickCount=2)
        await self.page.type('.pagination input[name="pageNo"]', str(page_num),
                             {'delay': self.login.input_time_random()})
        await self.page.click(".pagination button")

    async def _get_html(self, speed=1):
        """
        :param speed: 翻页间隔时间，秒
        :return: 返回爬取页面的HTML内容
        """
        sql = "select shop_id from shop_info where shop_id!='88888888'"  # 获取所有的店铺ID
        shop_infos = mysql.get_data(sql=sql, dict_result=True)
        shop_ids = []
        for shop_info in shop_infos:
            page_control = Format._read(shop_id=shop_info['shop_id'], flag="total_page")  # 获得存储在本地的店铺总的页码数量
            if not page_control:
                page_control = 1000  # 如果没有获取到页码总数，给个1000的总数

            shop_ids.append(shop_info['shop_id'])  # 将店铺ID存储起来用于后面重置翻页数据

            url = self.start_url.replace("shop", "shop" + shop_info["shop_id"])  # 获得到店铺首页url地址
            await self.page.goto(url)
            await self._jump_to_search_page()
            page_num = Format._read(shop_info['shop_id'], "page_num")  # 读取存储在本地的page_num

            while page_num < page_control:
                start_time = time.time()  # 本页面开始的时间存入变量

                try:
                    # if page_num:
                    await self._goto_last_page_num(page_num + 1)
                    await asyncio.sleep(5)
                    frames = self.page.frames
                    for f in frames:
                        if await f.J("#TPL_username_1"):
                            yield 0, 0
                    frame = await self.login.get_nc_frame(frames=frames)
                    if frame:
                        await self.login.slider(self.page, 1)

                except Exception as e:
                    print(e)
                    await asyncio.sleep(5)
                    continue
                try:
                    await self.page.waitForSelector(".shop-hesper-bd.grid")
                except errors.TimeoutError:
                    break
                except Exception as e:
                    print(e)
                    continue
                Format._write(shop_id=shop_info['shop_id'], flag="page_num", value=page_num + 1)  # 将下次需要爬取的页码存入本地的配件中
                page_num = Format._read(shop_info['shop_id'], "page_num")  # 读取下一次要爬取的页码

                yield await self.page.content(), shop_info['shop_id']  # 返回页面HTML内容和

                page_control = Format._read(shop_id=shop_info['shop_id'], flag="total_page")  # 获得存储在本地的店铺总的页码数量

                await asyncio.sleep(speed)  # 翻页间隔时间
                spent_time_this_page = time.time() - start_time  # 计算本页完成时间
                spent_time = Format._read(shop_id=shop_info['shop_id'], flag="spent_time")  # 读取上一次存储在本地的时间
                Format._write(shop_id=shop_info['shop_id'], flag="spent_time",
                              value=spent_time + spent_time_this_page)  # 将本页面完成时间加上后并存储在本地
            is_mail = Format._read(shop_info['shop_id'], "mail")
            if not is_mail:
                Reports().report(shop_info['shop_id'].split(" "))

        for shop_id in shop_ids:
            Format._del(shop_id=shop_id, flag="page_num")  # 重置翻页的数据
            Format._del(shop_id=shop_id, flag="total_page")  # 重置总页码数据
            Format._del(shop_id=shop_id, flag="mail")  # 重置邮件标记
            Format._del(shop_id=shop_id, flag="spent_time")  # 重置完成时间

    async def _parse(self):
        """
        解释_get_html中得到的HTML内容
        :return: 返回数据模型 item
        """
        item = {}
        async for html, ship_id in self._get_html(speed=10):
            if not html:
                yield 0
            doc = pq(html)
            total_page = Format._read(shop_id=ship_id, flag="total_page")
            if not total_page:
                num = doc(".pagination span.page-info").text()
                Format._write(shop_id=ship_id, flag="total_page", value=int(re.findall("/(\d+)", num)[0]))

            match = re.search("item\dline1", html).group()
            items = doc("." + match + " dl.item").items()
            for i in items:
                item['shop_id'] = ship_id
                item['link_id'] = i.attr("data-id")
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

    async def save(self):
        """
        处理_parse()中获得的数据模型，并写入到数据库中
        """
        async for i in self._parse():
            if not i:
                print("需要要切换淘宝账户")
                return 0
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
    loop = asyncio.get_event_loop()
    l = Login()
    b, p = loop.run_until_complete(l.login(**MY_TB_ACCOUNT))
    master = MasterSpider(b, p, l)
    loop.run_until_complete(master.save())
