from flask import Flask,jsonify,abort,request
import finalInterface as fI
import json
from flask_cors import *
import os
import glob
from datetime import timedelta
import pandas as pd
from celery import Celery
import pymysql
from kombu import Exchange, Queue


schedule_time = 300
jsonFilePath = '/Echarts/'

app = Flask(__name__)

CORS(app, supports_credentials=True)
def make_celery(app):
    celery = Celery("flaskTest",  # 此处官网使用app.import_name，因为这里将所有代码写在同一个文件flask_celery.py,所以直接写名字。
                    broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND']
                    )
    

    #schedule的任务专门有个worker执行
    queue = (
        Queue('schedule', Exchange('Exchange1', type='direct'), routing_key='queue_1_key'),
        Queue('default', Exchange('Exchange2', type='direct'), routing_key='queue_2_key')
    )
    route = {   
        'flaskTest.modifySQL': {'queue': 'schedule', 'routing_key': 'queue_1_key'},
         'flaskTest.downloadCityData': {'queue': 'default', 'routing_key': 'queue_2_key'}
    }
    celery.conf.update(CELERY_QUEUES=queue, CELERY_ROUTES=route,CELERYD_MAX_TASKS_PER_CHILD = 40)


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
    CELERY_BROKER_URL='amqp://guest:guest@localhost:5672/',
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
    facType  = request.args.get('facType')
    task = downloadCityData.delay(city,facType)
    insertIntoSQL(task.id,'waiting','0%',city,facType)
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
        resp = {'state':"success",'progress':'100%'}
    elif the_task.state == 'PENDING':   # 任务处于排队之中
        resp = {'state':'waiting','progress':'0%'}
    else:   
        resp = {'state':the_task.state,'progress':'0%'}
    return jsonify(resp)


@celery.task(bind = True)
def downloadCityData(self,city,facType):
    fI.getCityKNNData(city,facType,self)

def insertIntoSQL(taskId,progress,percent,city,facType):
    # 打开数据库连接
    db = pymysql.connect("localhost","root","a84615814","bishe",charset="utf8")
     
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    
    if progress == 'success':
        isFinished = 1
    else:
        isFinished = 0
    
    try:# 使用 execute()  方法执行 SQL 查询
        cursor.execute('insert into task values("%s", "%s","%s","%d","%s","%s")' % \
             (taskId, progress,percent,isFinished,city,facType))
        # 执行sql语句
        db.commit()
    except BaseException as e:
        print(e)
        # 发生错误时回滚
        db.rollback()  
    # 关闭数据库连接
    db.close()


def updateSQL(taskId,progress,percent):
    # 打开数据库连接
    db = pymysql.connect("localhost","root","a84615814","bishe",charset="utf8" )
     
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    if progress == 'success':
        isFinished = 1
    else:
        isFinished = 0
    
    try:# 使用 execute()  方法执行 SQL 查询
        cursor.execute("update task set progress='%s" % progress + "',percent='%s" % percent +"',isFinished='%d" % isFinished+ "' where task_id='%s" % taskId + "'")
        # 执行sql语句
        db.commit()
    except BaseException as e:
        print(e)
        # 发生错误时回滚
        db.rollback()  
    # 关闭数据库连接
    db.close()


#定时任务
#每5min进行更新
celery.conf.update(
    CELERYBEAT_SCHEDULE={
        'perminute': {
            'task': 'flaskTest.modifySQL',
            'schedule': timedelta(seconds=schedule_time),
            'args': ()
        }
    }
)

@celery.task
def modifySQL():
    # 打开数据库连接
    db = pymysql.connect("localhost","root","a84615814","bishe",charset="utf8" )

    #利用pandas 模块导入mysql数据
    dataSet=pd.read_sql('select * from task where isFinished = 0;',db)
    # 关闭数据库连接
    db.close()

    for indexs in dataSet.index: #逐行遍历
        task_id = dataSet.loc[indexs].values[0]
        the_task = downloadCityData.AsyncResult(task_id)   # 获取状态信息
        if  the_task.state=='PROGRESS':
            resp = {'state':'progress','progress':the_task.info.get('percent',0)}
        elif  the_task.state=='SUCCESS':
            resp = {'state':"success",'progress':'100%'}
        elif the_task.state == 'PENDING':   # 任务处于排队之中
            resp = {'state':'waitting','progress':'0%'}
        else:   
            resp = {'state':the_task.state,'progress':'0%'}
        updateSQL(task_id,resp['state'],resp['progress'])



@app.route('/update/')
def showTask():
     # 打开数据库连接
    db = pymysql.connect("localhost","root","a84615814","bishe",charset="utf8" )
    #利用pandas 模块导入mysql数据
    dataSet=pd.read_sql('select * from task where isFinished = 0;',db)
    result = []
    for indexs in dataSet.index: #逐行遍历
        task_id = dataSet.loc[indexs].values[0]
        progress = dataSet.loc[indexs].values[1]
        percent = dataSet.loc[indexs].values[2]
        isFinished = dataSet.loc[indexs].values[3]
        city = dataSet.loc[indexs].values[4]
        facType = dataSet.loc[indexs].values[5]
        dic = {'task_id':task_id,'progress':progress,'percent':percent,'isFinished':str(isFinished),'city':city,'facType':facType}
        result.append(dic)
    # 关闭数据库连接
    db.close()
    return json.dumps(result,ensure_ascii=False).encode("utf-8")



@app.route('/show/')
def showExitsFile():
    curpath = os.getcwd()
    path = curpath +os.path.sep+ 'Echarts'
    for root, dirs, files in os.walk(path):
        return json.dumps(files,ensure_ascii=False).encode("utf-8") #当前路径下所有非目录子文件 


@app.route('/getData/',methods=['POST'])
def getData():
    if not request.json:
        abort(400)
    curpath = os.getcwd()
    cityName = request.json['city']
    facType = request.json['facType']
    jsonData = []
    path = curpath+jsonFilePath+cityName+'-'+facType+'.json'
    if os.path.isfile(path):
        with open(path,"r",encoding="UTF-8") as f:
            jsonData = json.load(f)
        return json.dumps(jsonData,ensure_ascii=False).encode("utf-8")
    else:
        return json.dumps(jsonData,ensure_ascii=False).encode("utf-8")
    

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8383,debug=False)
