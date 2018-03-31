from flask import Flask,jsonify,abort,request
import finalInterface as fI
import json
from flask_cors import *

from celery import Celery
app = Flask(__name__)

CORS(app, supports_credentials=True)
def make_celery(app):
    celery = Celery("flaskTest",  # 此处官网使用app.import_name，因为这里将所有代码写在同一个文件flask_celery.py,所以直接写名字。
                    broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND']
                    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
app.config.update(
    CELERY_BROKER_URL='amqp://',
    CELERY_RESULT_BACKEND='amqp'
)

celery = make_celery(app)

@app.route('/getCityCenter/',methods=['POST'])
def getCityCenter():
    if not request.json or 'city' not in request.json:
        abort(400)
    cityName = request.json['city']
    result = fI.getCityCenter(cityName)
    resultJson = json.loads(result)
    resp = jsonify({'lng':resultJson['lng'],'lat':resultJson['lat']})
    return resp

@app.route('/download/',methods=['GET'])
def download():
    city  = request.args.get('city')
    facType = 'hospital'
    task = downloadCityData.delay(city,facType)
    return jsonify({'task_id':task.id}),202

#获取celery中任务执行情况Python
@app.route('/status/<task_id>')
def task_status(task_id):
    # 获取celery之中 task_id的状态信息
    the_task = downloadCityData.AsyncResult(task_id)   # 获取状态信息
    print("任务：{0} 当前的 state 为：{1}".format(task_id,the_task.state))
    if  the_task.state=='PROGRESS':
        resp = {'state':'progress','progress':the_task.info.get('percent',0)}
    elif  the_task.state=='SUCCESS':
        resp = {'state':"success",'progress':100}
    elif the_task.state == 'PENDING':   # 任务处于排队之中
        resp = {'state':'waitting','progress':0}
    else:   
        resp = {'state':the_task.state}
    return jsonify(resp)


@celery.task(bind = True)
def downloadCityData(self,city,facType):
    fI.getCityKNNData(city,facType,self)


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8383,debug=True)
