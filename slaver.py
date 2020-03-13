import mysql
import re
import asyncio
from settings import test_server, MY_TB_ACCOUNT
from Login_New import Login

test_server['db'] = "test"


class Slaver(object):
    url = "https://item.taobao.com/item.htm?id="

    def __init__(self, b=None, p=None, l=None):
        self.browser = b
        self.page = p
        self.login = l
        pass

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

    async def _get_html(self):
        for item in self._get_item():
            # url = self.url + item['link_id']
            url = self.url + "586886697621"
            while 1:
                try:
                    await self.page.goto(url=url)
                    await asyncio.sleep(5)
                    frames = self.page.frames
                    for f in frames:
                        if await f.J("#TPL_username_1"):
                            await f.type("#TPL_username_1", MY_TB_ACCOUNT['username'],
                                         {"delay": self.login.input_time_random()})
                            await f.type("#TPL_password_1", MY_TB_ACCOUNT['password'],
                                         {"delay": self.login.input_time_random()})
                            if await f.J("#nc_1_n1z"):
                                await self.login.slider(self.page, 1)
                            await f.click("#J_SubmitStatic")
                            break
                    frame = await self.login.get_nc_frame(frames=frames)
                    if frame:
                        await self.login.slider(self.page, 1)
                    await self.page.waitForSelector("#detail")
                    break
                except Exception as e:
                    print(e)
                    await asyncio.sleep(5)
                    continue
            yield await self.page.content(), item

    async def parse(self):
        async for html, item in self._get_html():
            a = re.findall('";(.*?);".*?e":"(\d+\.\d+).*?skuId":"(\d+)', html)
            if a:
                # discount = 0
                # if item['promotionPrice']:
                #     discount = round(item['promotionPrice'] - item['price'], 2)
                for i in range(len(a)):
                    item['price'] = a[i][1]
                    item['skuId'] = a[i][2]
                    # if discount:
                    #     item['promotionPrice'] = item['price'] - discount
                    print(item)
        input()


# res = requests.get("https://item.taobao.com/item.htm?id=%s" % (str(link_id)))
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    l = Login()
    b, p = loop.run_until_complete(l.login(**MY_TB_ACCOUNT))
    s = Slaver(b, p, l)
    loop.run_until_complete(s.parse())
