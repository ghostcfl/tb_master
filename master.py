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

    def __init__(self):
        pass

    @staticmethod
    def _get_curls(shop_id):
        curls = []
        results = mysql.get_data(db=test_server, t="tb_search_curl", c={'shop_id': shop_id}, dict_result=True)
        for res in results:
            curls.append(res)
        return curls

    @staticmethod
    def format_request_params(curl, page_num=2):
        curl = re.sub("\"|\^", "", curl)
        a = curl.split(" -H ")
        params = {}
        cookies = {}
        headers = {}
        url = ""
        for b in a:
            if re.match("curl", b):
                c = b.split(" ")[-1]
                url = c.split("?", 1)[0]
                d = c.split("?", 1)[1].split("&")
                for e in d:
                    f = e.split("=", 1)
                    params[f[0]] = f[1]
            elif re.match("Cookie", b, re.I):
                g = b.split(": ")[-1]
                h = g.split("; ")
                for i in h:
                    j = i.split("=", 1)
                    cookies[j[0]] = j[1]
            else:
                k = b.split(": ", 1)
                headers[k[0]] = k[1]
        params['orderType'] = "hotsell_desc"
        if page_num > 1:
            headers['Referer'] = re.sub("i\/asynS", "s", url) + "?" + "&".join(
                [k + "=" + str(v) for k, v in params.items()]) + "&pageNo=" + str(page_num)
            params['pageNo'] = str(page_num)
        return url, params, cookies, headers

    @staticmethod
    def _get_shop_id():
        sql = "select shop_id from shop_info where shop_id!='88888888'"  # 获取所有的店铺ID
        shop_infos = mysql.get_data(sql=sql, dict_result=True)
        for shop_info in shop_infos:
            if shop_info['shop_id'] == "115443253":
                yield shop_info['shop_id']

    @staticmethod
    def _get_page_num(shop_id):
        result = mysql.get_data(db=test_server, t="tb_search_page_info", c={"shop_id": shop_id}, dict_result=True)
        if not result:
            d = {
                "shop_id": shop_id,
                "total_page": 100,
                "used_page_nums": "0"
            }
            mysql.insert_data(db=test_server, t="tb_search_page_info", d=d)
            result = mysql.get_data(db=test_server, t="tb_search_page_info", c={"shop_id": shop_id}, dict_result=True)

        used_page_nums = [int(x) for x in result[0]['used_page_nums'].split(",")]
        used_page_nums.sort()
        total_page = result[0]['total_page']
        set_a = set([i for i in range(total_page + 1)])
        set_b = set(used_page_nums)
        list_result = list(set_a - set_b)
        if list_result:
            return random.choice(list_result), used_page_nums, total_page
        else:
            return 0, 0, 0

    def _get_html(self):
        for shop_id in self._get_shop_id():
            curls = self._get_curls(shop_id)
            curl = random.choice(curls)
            page_num, used_page_nums, total_page = self._get_page_num(shop_id)
            if not page_num:
                continue
            url, params, cookies, headers = self.format_request_params(curl['curl'], page_num)
            print(headers)
            proxies = {"https": "http://58.218.92.142:9150"}
            exit(0)
            r = requests.get(url=url, params=params, cookies=cookies, headers=headers,proxies=proxies)
            html = r.text.replace("\\", "")
            html = re.sub("jsonp\d+\(\"|\"\)", "", html)
            for k, v in params.items():
                print(k, end=":")
                print(v, end=":")
            yield html, shop_id, curl, page_num, used_page_nums, total_page

    def _parse(self):
        for html, shop_id, curl, page_num, used_page_nums, total_page in self._get_html():
            doc = PyQuery(html)
            #  存在未知错误的时候，写错误的HTML写到文件中
            try:
                match = re.search("item\dline1", html).group()
            except Exception as e:
                logger.error(e)
                with open("error.html", 'w') as f:
                    f.write(html)
                logger.error("未知错误查看error.html文件1")
                mysql.delete_data(db=test_server, t='tb_search_curl', c={"id": curl['id']})
                continue
            if not match:
                with open("error.html", 'w') as f:
                    f.write(html)
                logger.error("未知错误查看error.html文件2")

            used_page_nums.append(page_num)
            num = doc(".pagination span.page-info").text()
            tspi = {  # tb_search_page_info
                "shop_id": shop_id,
                "total_page": re.search("\d+\/(\d+)", num).group(1),
                "used_page_nums": ",".join([str(x) for x in used_page_nums]),
            }
            mysql.update_data(db=test_server, t="tb_search_page_info", set=tspi, c={"shop_id": shop_id})
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



# import requests
# import re
#
# curl = 'curl "https://shop68559944.taobao.com/i/asynSearch.htm?_ksTS=1584414011939_808&callback=jsonp809&mid=w-16659046903-0&wid=16659046903&path=/search.htm&search=y&spm=a1z10.3-c-s.w4002-16659046903.31.199525e9yYUqQN&orderType=hotsell_desc&pageNo=4" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" -H "Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2" --compressed -H "Connection: keep-alive" -H "Cookie: enc=0G0Ym07eazGeaU4apn991R3TQsQbY2nDzl2wP1gVuYOMBDTkEesj5swMtywhQMgZFOrbH"%"2BKwWGBpdLI"%"2Bv3bcVQ"%"3D"%"3D; thw=cn; _m_h5_tk=522974ff5f7934c9f2ee66d99025b354_1584434156027; _m_h5_tk_enc=12a2812233ec7841e781c149b2c0d535; sgcookie=ENRpVB9vZ2"%"2FiPRnqfMJmD; tfstk=cJpNBQN7vAHZFYNkoTWVle6Vkz1OZzJkHySfsQcdYbvx095hiFaAxgslT_NxH1f..; pnm_cku822=098"%"23E1hvxpvUvbpvUpCkvvvvvjiPn2Fp1jYPP2dOQjYHPmPpQjiWP2sygjDPRLsyAjlPR4wCvvpvvUmm2QhvCPMMvvvCvpvVvmvvvhCvkphvC9QvvOCzpTyCvv9vvUvgi"%"2BD6RfyCvmFMMQCGS6vvgQvv9DCvpvo"%"2BvvmmZhCv2CUvvUEpphvWwpvv9D3vpvA1mphvLvseppvjOg2vqU0QKoZHtRFEDLuTWDAvD7zhV4tYVVzhAj7xhBwl"%"2BExrg8TJEcqhAj7gKL9"%"2BBaV9kUkZHkx"%"2FAjc6D46wjLPEDaexRfytvpvhvvvvvv"%"3D"%"3D; hibext_instdsigdipv2=1; t=2e904a7ddd36ecedf9084957aa2faee3; UM_distinctid=170ae018399245-0386396cd3d6e18-4c302879-13c680-170ae01839b1ae; mt=ci=0_0; isg=BMLCudMKKO3GWjSxI-B2iGa2EMgkk8atlr0VCwzb7jXgX2LZ9CMWvUg9C9sjFD5F; l=dBEhyV54Qyaozg02BOCCIFJ2en7OSIOYYuJNuLLvi_5CV6Y6O7_OorHC9Fv6VsWfT2LB4HrbH8p9-etkNQMmndhUOyjADxDc.; cna=hFCkFgfnYSQCAXFu01veEKo2; cookie2=1ad4f1a27d229546b21e420af6167a67; _tb_token_=e53e33193b1bf; v=0; hng=CN"%"7Czh-CN"%"7CCNY"%"7C156; _samesite_flag_=true; unb=2206498784722; sn=selingna5555"%"3Atest; uc1=cookie21=U"%"2BGCWk"%"2F7oPIg&cookie14=UoTUPvQVPDVwWg"%"3D"%"3D; csg=b1f8b152; _cc_=V32FPkk"%"2Fhw"%"3D"%"3D; skt=69e3bc85953b8f0b; ext_pgvwcount=2" -H "Upgrade-Insecure-Requests: 1" -H "TE: Trailers"'
#
#
# def format_request_params(curl):
#     curl = re.sub("\"", "", curl)
#     a = curl.split(" -H ")
#     params = {}
#     cookies = {}
#     headers = {}
#     for b in a:
#         # print(b)
#         if re.match("curl", b):
#             c = b.split(" ")[-1]
#             url = c.split("?", 1)[0]
#             d = c.split("?", 1)[1].split("&")
#             for e in d:
#                 f = e.split("=", 1)
#                 params[f[0]] = f[1]
#         elif re.match("Cookie", b):
#             g = b.split(": ")[-1]
#             h = g.split("; ")
#             for i in h:
#                 j = i.split("=", 1)
#                 cookies[j[0]] = j[1]
#         else:
#             k = b.split(": ", 1)
#             headers[k[0]] = k[1]
#             # print(h)
#     return url, params, cookies, headers
#
#
# url, params, cookies, headers = format_request_params(curl)
# # for k, v in cookies.items():
# #     print(k + " " + v)
# r = requests.get(url, headers=headers, params=params, cookies=cookies)
# print(r.text)
# import asyncio
# from pyppeteer import launch
# from settings import dev
#
# url = "https://szsaibao.taobao.com/search.htm?spm=a1z10.3-c-s.w4002-21808473997.28.35632d90dC9V0o&_ksTS=1584680372583_750&callback=jsonp751&input_charset=gbk&mid=w-21808473997-0&wid=21808473997&path=%2Fsearch.htm&search=y&orderType=hotsell_desc&pageNo=3"
#
#
# async def run():
#     b = await launch(dev)
#     p = await b.newPage()
#     await p.setViewport({"width": 1440, "height": 900})
#     await p.goto(url)
#     await p.waitForSelector(".shop-hesper-bd.grid",timeout=0)
#     cookie = await p.cookies()
#     print(cookie)
#
# if __name__ == '__main__':
#     asyncio.run(run())
# cookies = [{'name': 'l', 'value': 'dBTFO_L4Q1QLQLwEBOCg-FJ2wsbOSIRAguJNua3Hi_5QE681Fb_OozL09FJ6VjWftZYB4-9jaL29-etkZQDmndFM93Rw_xDc.', 'domain': '.taobao.com', 'path': '/', 'expires': 1600247232, 'size': 98, 'httpOnly': False, 'secure': False, 'session': False}, {'name': '_m_h5_tk_enc', 'value': '005d496ad4fc316097d34df926297952', 'domain': '.taobao.com', 'path': '/', 'expires': 1585300015.190792, 'size': 44, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'isg', 'value': 'BIyMWO--PqtlmCrXEaNgQEX2Xeq-xTBvHumx9-ZNmDfacSx7DtUA_4LDFXnJOWjH', 'domain': '.taobao.com', 'path': '/', 'expires': 1600247232, 'size': 67, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'uc1', 'value': 'cookie14=UoTUPvbEMOMRWQ%3D%3D&lng=zh_CN', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 42, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'tfstk', 'value': 'ctlhBnfx8vyBDnBPh9NIPZaFDbRAZB7av0oI_XjTnQP0CJcNiX6N3Db9Ilq5_T1..', 'domain': '.taobao.com', 'path': '/', 'expires': 1600247212, 'size': 70, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'v', 'value': '0', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 2, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'cna', 'value': 'nXX7FveVhAcCAXFusEjwsp5o', 'domain': '.taobao.com', 'path': '/', 'expires': 2215415211, 'size': 27, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'skt', 'value': 'c62b0734f3bad2dc', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 19, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'sn', 'value': 'simpleli%3A%E6%A2%81%E7%A5%A5%E5%81%A5', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 40, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_tb_token_', 'value': 'e881854fe5e39', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 23, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'unb', 'value': '2204928296721', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 16, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'sgcookie', 'value': 'EkVfHPG1Nf7UM9LF%2F5I8N', 'domain': '.taobao.com', 'path': '/', 'expires': 1616231211.832112, 'size': 31, 'httpOnly': True, 'secure': False, 'session': False}, {'name': 'cookie2', 'value': '1fe82b1f3376d91898c5b3bcab61370c', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 39, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'x', 'value': '31295113', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 9, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_samesite_flag_', 'value': 'true', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 19, 'httpOnly': True, 'secure': True, 'session': True}, {'name': 'csg', 'value': 'df54c6df', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 11, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_m_h5_tk', 'value': 'cf154e8be6d7732ec0a1372eb198f3f0_1584702775081', 'domain': '.taobao.com', 'path': '/', 'expires': 1585300015.190717, 'size': 54, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 't', 'value': '4e92cac1d1650b21ad01669d69c54b5f', 'domain': '.taobao.com', 'path': '/', 'expires': 1592471198.804966, 'size': 33, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'pnm_cku822', 'value': '', 'domain': 'szsaibao.taobao.com', 'path': '/', 'expires': 1587287230, 'size': 10, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'thw', 'value': 'cn', 'domain': '.taobao.com', 'path': '/', 'expires': 1616231194.192734, 'size': 5, 'httpOnly': False, 'secure': False, 'session': False}]
# cookie = {}
# for x in cookies:
#     if x['name'] != 'sn':
#         cookie[x['name']] = x['value']
#
# import requests
# headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0', 'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01', 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2 --compressed', 'Referer': 'https://shop115443253.taobao.com/search.htm?_ksTS=1584682864154_932&callback=jsonp933&mid=w-9539895920-0&wid=9539895920&path=/search.htm&search=y&orderType=hotsell_desc&pageNo=40', 'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'TE': 'Trailers'}
# print(cookie)
# r = requests.get(url="https://szsaibao.taobao.com/i/asynSearch.htm?mid=w-21808473997-0&path=/search.htm&search=y&input_charset=gbk&orderType=hotsell_desc&pageNo=3", headers=headers, cookies=cookie)
# print(r.text)
# # _ksTS=1584692676219_750&callback=jsonp751