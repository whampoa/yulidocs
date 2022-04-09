from flask import Blueprint, Flask, render_template, request
from werkzeug.utils import secure_filename
from flask import jsonify
from flask_cors import cross_origin
import os
from test2 import main

# 新建flask应用
app = Flask(__name__)
# 新建上下文为/yuli的BluePrint
bp = Blueprint('yuli', __name__, url_prefix='/yuli', template_folder='templates', static_folder='')


# 首页路径
@bp.route('/')
def home():
    # 返回首页视图
    return render_template('index.html')


# 文件上传与预测
@bp.route('/file', methods=['POST'])
# 实现跨域
@cross_origin(supports_credentials=True)
def add_file():
    # 文件上传
    try:
        file = request.files['file']
        root_path = os.path.dirname(__file__)
        upload_path = os.path.join(root_path, 'temp', secure_filename(file.filename))
        file.save(upload_path)
    except Exception:
        return jsonify({'code': 1, 'msg': 'File upload fail!', 'data': None})

    # 预测程序执行
    try:
        res = main(['', upload_path])
    except Exception:
        print("except in predict")
        return jsonify({'code': 0, 'msg': 'Connection OK', 'data': []})

    # 结果返回
    print('return')
    return jsonify({'code': 0, 'msg': 'Connection OK', 'data': res.split('\n')[:-1]})


# flask应用注册/yuli对应的blueprint，register必须在指定route之后才能生效
app.register_blueprint(bp)

if __name__ == '__main__':
    # 启动flask应用
    app.run()
