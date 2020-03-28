import mysql
import datetime
from settings import test_server
from smtp import mail
from settings import my_user

test_server['db'] = 'test'


class Reports(object):
    translate_dictionary = {
        "insert": "新增",
        "price": "更新销售价格",
        "promotion": "更新优惠价格",
        "sale": "更新销量",
        "XiaJia": "下架商品",
        "ShangJia": "重新上架商品",
    }

    def get(self, shop_ids):
        shop_report_groups = []
        for shop_id in shop_ids:
            shop_name = mysql.get_data(
                sql="SELECT shopname FROM shop_info WHERE shop_id={}".format(shop_id),
                return_one=True
            )
            flag_report_groups = []
            # sql = "SELECT COUNT(id) AS nums FROM tb_master where shop_id='{}' and update_date<'{}'".format(shop_id,
            #                                                                                                datetime.date.today())
            # nums = mysql.get_data(db=test_server, sql=sql, return_one=True)
            # if int(nums) > 0:
            #     flag_report_groups.append("下架商品{}条".format(nums))
            # del sql
            # del nums
            for flag in self.translate_dictionary.keys():
                sql = "SELECT COUNT(id) AS nums FROM tb_master WHERE flag LIKE '%%{}%%' AND shop_id='{}'".format(flag,
                                                                                                                 shop_id)
                nums = mysql.get_data(db=test_server, sql=sql, return_one=True)
                if int(nums) > 0:
                    flag_report_groups.append("{}{}条".format(self.translate_dictionary[flag], nums))

            if flag_report_groups:
                result = mysql.get_data(db=test_server, t="tb_search_page_info",
                                        c={"shop_id": shop_id}, dict_result=True)
                flag_report_groups.append("总计爬取{}页".format(result[0]['total_page']))
                flag_report_groups.append(
                    "总计花费{}分{}秒".format(int(result[0]['spent_time'] / 60), int(result[0]['spent_time'] % 60)))
                flag_report_groups.reverse()
                flag_report_groups.append(shop_name)
                flag_report_groups.reverse()
                shop_report_groups.append("|".join(flag_report_groups))

        return "\n".join(shop_report_groups)

    def report(self, shop_ids):
        r = self.get(shop_ids=shop_ids)
        print(r)
        mail("店铺搜索页爬虫报告", r, my_user)
        # [Format._write(shop_id=shop_id, flag="mail", value=1) for shop_id in shop_ids]


if __name__ == '__main__':
    report = Reports()
    ids = ["115443253", "33817767", "34933991", "131282813", "68559944", "60299985", "197444037"]
    report.report(ids)
