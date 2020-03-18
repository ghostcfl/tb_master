import re
import mysql
from flask import Flask, render_template, request
from settings import test_server

test_server['db'] = 'test'
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', result={"status": ""})


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        result = request.form
        item = result.to_dict()
        item['curl'] = item['curl'].strip()
        if not re.match("^curl", item['curl']):
            return render_template("index.html", result={"status": "传送的数据不正确"})
        shop_id_match = re.search("shop(\d+)\.", item['curl'])
        if shop_id_match:
            item['shop_id'] = shop_id_match.group(1)
        mysql.insert_data(db=test_server, t='tb_search_curl', d=item)
    return render_template('index.html', result={"status": "写入数据库成功"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10200)
