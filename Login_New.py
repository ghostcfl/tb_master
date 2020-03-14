import asyncio, re, random, mysql, time
from pyppeteer.launcher import launch
from pyppeteer import errors
from settings import dev, LINUX, test_server as ts, width, height
from Format import sleep, net_check, time_now
from logger import get_logger
from settings import STORE_INFO, MY_TB_ACCOUNT

# from spider import Spider

logger = get_logger()


class Login(object):
    b = None

    async def get_page(self, **kwargs):
        # dev['args'].append(kwargs['window_position'])
        self.b = await launch(**dev)
        p = await self.b.pages()
        p = p[0]
        await p.setViewport({"width": width, "height": height})
        return p

    async def login(self, **kwargs):
        p = await self.get_page(**kwargs)
        while 1:
            try:
                await p.goto("https://login.taobao.com", timeout=30000)
            except errors.PageError:
                logger.warning("网络异常5秒后重连")
                sleep(5)
            except errors.TimeoutError:
                logger.warning("网络异常5秒后重连")
                sleep(5)
            else:
                break

        while True:
            try:
                await p.waitForSelector(".forget-pwd.J_Quick2Static", visible=True, timeout=10000)
                await p.click(".forget-pwd.J_Quick2Static")
            except errors.TimeoutError:
                pass
            except errors.ElementHandleError:
                await p.reload()
                continue
            finally:
                try:
                    await p.type('#TPL_username_1', kwargs['username'], {'delay': self.input_time_random() - 50})
                    await p.type('#TPL_password_1', kwargs['password'], {'delay': self.input_time_random()})
                except errors.ElementHandleError:
                    await p.reload()
                else:
                    break

        net_check()
        # 检测页面是否有滑块。原理是检测页面元素。
        try:
            await p.waitForSelector('#nc_1_n1z', visible=True, timeout=3000)
        except errors.TimeoutError:
            slider = 0
        else:
            slider = await p.J('#nc_1_n1z')
        if slider:
            print("出现滑块情况判定")
            t = await self.slider(p=p)
            if t:
                return self.b, p, t
            await p.click("#J_SubmitStatic")  # 调用page模拟点击登录按钮。
            time.sleep(2)
            await self.get_cookie(p)
        else:
            await p.click("#J_SubmitStatic")

        try:
            await p.waitForNavigation()
        except errors.TimeoutError:
            pass
        print("登录成功")
        return self.b, p

    async def get_cookie(self, page):
        """获取登录后cookie"""
        cookies_list = await page.cookies()
        cookies = ''
        for cookie in cookies_list:
            str_cookie = '{0}={1};'
            str_cookie = str_cookie.format(cookie.get('name'), cookie.get('value'))
            cookies += str_cookie
        return cookies

    async def phone_verify(self, p):
        try:
            await p.waitForSelector("#container", timeout=120000)
        except errors.TimeoutError:
            logger.info("超时末扫码或需要手机验证！")
            await self.verify(p)
            net_check()
            await p.goto("https://myseller.taobao.com/home.htm")
        finally:
            await p.waitForSelector("#container", timeout=0)
            content = await p.content()
            a = re.search('nick: "(.*?):', content)
            b = re.search('nick: "(.*?)"', content)
            if a:
                account = a.group(1)
            else:
                account = b.group(1)
            if account == "arduino_sz":
                logger.info("开源电子登陆成功")
                f = "KY"
            elif account == "玉佳电子科技有限公司":
                logger.info("玉佳企业店登陆成功")
                f = "YK"
            elif account == "simpleli":
                logger.info("赛宝电子登陆成功")
                f = "TB"
            elif account == "selingna5555":
                logger.info("玉佳电子登陆成功")
                f = "YJ"
            else:
                logger.info('登陆账户信息获取失败，即将重启爬虫！')
                await self.b.close()
                await self.login()
            try:
                net_check()
                await p.goto("https://trade.taobao.com/trade/itemlist/list_sold_items.htm")
                await p.waitForSelector(".pagination-mod__show-more-page-button___txdoB", timeout=30000)
            except errors.TimeoutError:
                await self.verify(p)
                net_check()
                await p.goto("https://trade.taobao.com/trade/itemlist/list_sold_items.htm")
                await p.waitForSelector(".pagination-mod__show-more-page-button___txdoB", timeout=30000)
            finally:
                net_check()
                await p.click(".pagination-mod__show-more-page-button___txdoB")  # 显示全部页码
                t = await self.slider(p)
                if t:
                    return t
                else:
                    return f

    @staticmethod
    async def get_nc_frame(frames):
        for frame in frames:
            slider = await frame.J("#nc_1_n1z")
            if slider:
                return frame
        return None

    async def slider(self, p, must_check=0):
        await asyncio.sleep(3)
        frames = p.frames
        if must_check:
            while 1:
                frame = await self.get_nc_frame(frames)
                if frame:
                    break
        else:
            frame = await self.get_nc_frame(frames)
        if frame:
            nc = await frame.J("#nc_1_n1z")
            nc_detail = await nc.boundingBox()
            print(nc_detail)
            x = int(nc_detail['x'] + 1)
            y = int(nc_detail['y'] + 1)
            width = int(nc_detail['width'] - 1)
            height = int(nc_detail['height'] - 1)
            logger.info("条形验证码")
            try_times = 0
            while 1:
                logger.info("第" + str(try_times) + "次尝试滑动验证码")
                if try_times > 10:
                    logger.info("滑动失败退出")
                    return 1
                try_times += 1
                await asyncio.sleep(1)
                start_x = random.uniform(x, x + width)
                start_y = random.uniform(y, y + height)
                a = y - start_y
                # await frame.hover("#nc_1_n1z")
                await p.mouse.move(start_x, start_y)
                await p.mouse.down()
                await p.mouse.move(start_x + random.uniform(300, 400),
                                   start_y + random.uniform(a, 34 - abs(a)),
                                   {"steps": random.randint(30, 100)})
                await p.mouse.up()
                while 1:
                    try:
                        frame.waitForSelector(".nc-lang-cnt a", timeout=10000)
                        await asyncio.sleep(2)
                        await frame.click(".nc-lang-cnt a:first-child")
                        break
                    except errors.TimeoutError:
                        await asyncio.sleep(1)
                        slider = await frame.J("#nc_1_n1z")
                        if not slider:
                            logger.info("滑动成功1")
                            await asyncio.sleep(5)
                            frame = await self.get_nc_frame(frames)
                            if not frame:
                                return 0
                    except errors.PageError:
                        await asyncio.sleep(1)
                        slider = await frame.J("#nc_1_n1z")
                        if not slider:
                            logger.info("滑动成功2")
                            await asyncio.sleep(5)
                            frame = await self.get_nc_frame(frames)
                            if not frame:
                                return 0

    async def verify(self, p):
        try:
            await p.waitForSelector("div.aq_overlay_mask", timeout=10000)
        except errors.TimeoutError:
            pass
        else:
            logger.info("需要要手机验证码")
            if LINUX:
                test_server = ts.copy()
                test_server['db'] = "test"
                id = random.randint(0, 100)
                mysql.insert_data(db=test_server, t="phone_verify", d={"id": id})
                frames = p.frames
                net_check()
                verify_code = "0"
                while True:
                    net_check()
                    await frames[1].click(".J_SendCodeBtn")
                    for i in range(120):
                        await asyncio.sleep(5)
                        res = mysql.get_data(db=test_server, cn=["verify_code"],
                                             t="phone_verify", c={"id": id}, )
                        verify_code = res[0][0]
                        if verify_code != "0":
                            mysql.delete_data(db=test_server, t="phone_verify", c={"id": id})
                            break
                    if verify_code != "0":
                        break
                    await asyncio.sleep(10)
            else:
                frames = p.frames
                net_check()
                await frames[1].click(".J_SendCodeBtn")
                verify_code = input(time_now() + " | 请输入6位数字验证码：")

            # await frames[1].click(".J_SendCodeBtn")
            # verify_code = input(time_now() + " | 请输入6位数字验证码：")
            await frames[1].type(".J_SafeCode", verify_code, {'delay': self.input_time_random() - 50})
            net_check()
            await frames[1].click("#J_FooterSubmitBtn")

    def input_time_random(self):
        return random.randint(100, 151)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ss = Login()
    b, p = loop.run_until_complete(ss.login(**MY_TB_ACCOUNT))
