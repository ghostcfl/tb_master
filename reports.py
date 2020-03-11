import mysql
import Format
from settings import test_server
from smtp import mail
from settings import my_user

test_server['db'] = 'test'


class Reports(object):

    def get(self, shop_ids, flags):

        shop_report_groups = []
        for shop_id in shop_ids:
            shop_name = mysql.get_data(
                sql="SELECT shopname FROM shop_info WHERE shop_id={}".format(shop_id),
                return_one=True
            )
            flag_report_groups = []
            for flag in flags:
                sql = "SELECT COUNT(id) AS nums FROM tb_master WHERE flag LIKE '%%{}%%' AND shop_id='{}'".format(flag,
                                                                                                                 shop_id)
                nums = mysql.get_data(db=test_server, sql=sql, return_one=True)
                if int(nums) > 0:
                    flag_report_groups.append("{}{}条".format(self._flag_translation(flag), nums))
            if flag_report_groups:
                page_num = Format._read(shop_id, "page_num")
                flag_report_groups.append("总计爬取{}页".format(page_num))
                spent_time = Format._read(shop_id, "spent_time")
                flag_report_groups.append("总计花费{}分{}秒".format(int(spent_time / 60), int(spent_time % 60)))
                flag_report_groups.reverse()
                flag_report_groups.append(shop_name)
                flag_report_groups.reverse()
                shop_report_groups.append("|".join(flag_report_groups))

        return "\n".join(shop_report_groups)

    @staticmethod
    def _flag_translation(flag):
        translate_dictionary = {
            "insert": "新增",
            "price": "更新销售价格",
            "promotion": "更新优惠价格",
            "sale": "更新销量",
        }
        return translate_dictionary[flag]

    def report(self, shop_ids):
        flags = ["insert", "price", "promotion", "sale"]
        r = self.get(shop_ids=shop_ids, flags=flags)
        mail("店铺搜索页爬虫报告", r, my_user)
        [Format._write(shop_id=shop_id, flag="mail", value=1) for shop_id in shop_ids]


if __name__ == '__main__':
    pass
