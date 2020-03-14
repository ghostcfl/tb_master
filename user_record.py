import asyncio
import mysql
from pyppeteer import launch
from settings import dev
from matplotlib import pyplot as plt, image as mpimg


async def run():
    b = await launch(**dev)
    p = await b.newPage()


    await p.setViewport({"width": 1440, "height": 900})
    await p.goto("https://login.taobao.com")
    ms = await p.J(".module-static")
    if ms:
        ls = await p.J(".login-switch")
        box = await ls.boundingBox()
        await p.mouse.click(box['x'] + 10, box['y'])
    while 1:
        try:
            await p.waitForSelector("#J_QRCodeImg")
            image = await p.J("#J_QRCodeImg")
            await image.screenshot({'path': './qrcode.png'})
        except Exception as e:
            pass
        else:
            break

    qrcode = mpimg.imread('qrcode.png')  # 读取和代码处于同一目录下的 qrcode.png
    plt.imshow(qrcode)  # 显示图片
    plt.axis('off')  # 不显示坐标轴
    plt.show()

    await p.waitForNavigation()
    start_url = 'https://shop.taobao.com/'
    sql = "select shop_id from shop_info where shop_id!='88888888'"  # 获取所有的店铺ID
    shop_infos = mysql.get_data(sql=sql, dict_result=True)
    item = {}
    for shop_info in shop_infos:
        url = start_url.replace("shop", "shop" + shop_info["shop_id"])
        await p.goto(url)
        await p.waitForSelector(".all-cats-trigger.popup-trigger")
        await p.click(".all-cats-trigger.popup-trigger")
        item['user_agent'] = await b.userAgent()
        cookies = await p.cookies()
        item['cookies'] = ";".join([c['name']+"="+c['value'] for c in cookies])
        item['refer'] = p.url
        print(item)
        break


if __name__ == '__main__':
    asyncio.run(run())
