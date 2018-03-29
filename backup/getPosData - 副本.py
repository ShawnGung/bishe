import getParams as gp #调用获取子级城市的模块
import requests
import urllib.parse
import json
import pandas as pd
import time
import sys
from queue import Queue


GDkey = gp.getGDkey()
disParam = gp.getDisParam()
time_start = 0
time_end  = 0
global failTimes
failTimes = 100
global akQueue
akQueue = gp.getAkQueue()#ak的队列
global ak
ak = akQueue.get()
global maxLat,minLat,maxLng,minLng
global cityList #城市list
global oneCity #当前城市名称
global FaN #当前设备名称
global FList #设备list
global lat #当前纬度
global lng #当前经度



def get_post_data(url):
    # 首先获取到登录界面的html
    r = requests.get(url)
    return r.text

def get_urlencode_params(oneCity):
    values={}
    values['keywords'] = oneCity
    params=urllib.parse.urlencode(values)
    return params


#获取该城市的经纬度范围
#return maxLat,minLat,maxLng,minLng
def getRange(oneCity):
    latList = []
    lngList = []
    params = get_urlencode_params(oneCity)
    url = 'http://restapi.amap.com/v3/config/district?key=' + GDkey + '&' + params + '&output=json'
    jsonData = get_post_data(url)
    data = json.loads(jsonData)
    for each in data['districts'][0]['districts']:
        lng,lat = each['center'].split(',')
        latList.append(lat)
        lngList.append(lng)
    return gp.str2float(max(latList)),gp.str2float(min(latList)),gp.str2float(max(lngList)),gp.str2float(min(lngList))


#最外层遍历设施
def getFacilityNum():
    global FList
    FList = gp.get_facility()#设施的列表
    while len(FList)>0: #按照栈来进行处理
        global FaN
        FaN = FList.pop()
        getPosData(FaN)

#遍历经纬度
def getPosData(FaN):
    values={}
    posResults=[] #数量的Results
    posResults.append([])#纬度
    posResults.append([])#经度
    posResults.append([])#数量
    global cityList
    global lat #当前纬度
    global lng #当前经度
    cityList = gp.getCityList()
    global ak
    #for oneCity in cityList:
    while len(cityList)>0 :
        global oneCity
        oneCity = cityList.pop()
        global maxLat,minLat,maxLng,minLng
        maxLat,minLat,maxLng,minLng = getRange(oneCity)
        latRange = int((maxLat-minLat) // disParam)
        lngRange = int((maxLng-minLng) // disParam)
        for i in range(0,latRange):
            for j in range(0,lngRange):
                lat = round(i*disParam + minLat,3)
                lng = round(j*disParam + minLng,3)
                values['query'] = FaN
                params = urllib.parse.urlencode(values)
                url = 'http://api.map.baidu.com/place/v2/search?'+ params+'&location='+str(lat)+','+str(lng)+\
                    '&radius=' + str(gp.getMetParam()) + '&output=json&ak='+ ak +'&page_size=20&page_num=0'
                posResults = waitRequest(url,posResults,FaN)
                if i*j % 100 == 0 and i!=0 and j!=0:#每100次存储一次数据
                    saveInCsv(posResults,FaN)


#保存到csv文件中 
#facility 是设施名字
def saveInCsv(results,facility):
    oriData = loadFromCsv()
    #转换为dataframe
    reDataFrame = pd.DataFrame({'lat':results[0],'lng':results[1],'total':results[2]})
    #合并
    finData = oriData.append(reDataFrame)
    finData.to_csv(facility + '.csv',index=False)
    dictReset(results)
    print('saved')


#重置results
def dictReset(results):
    results.clear()
    results.append([])#纬度
    results.append([])#经度
    results.append([])#数量

#首先读取原来的csv
def loadFromCsv():
    try:
        global FaN
        f=open(FaN+'.csv') #解决pandas读取中文名的文件名问题
        data = pd.read_csv(f,encoding='utf-8') #解决编码问题utf-8
        return data
    except:
        return pd.DataFrame()

#超过并发量,等待后请求
#进行五次等待，每次等待2s
def waitRequest(url,posResults,FaN):
    global lat #当前纬度
    global lng #当前经度
    for waitCount in range(0,5):
        jsonData = get_post_data(url)
        dictData = json.loads(jsonData)
        if dictData['message'] == 'ok' and dictData['status'] == 0:
            failTimes = 100 #成功一次后重新刷新，如果连续100次都失败，更换ak
            if judgeTotal(dictData['total']):
                posResults[0].append(lat)
                posResults[1].append(lng)
                posResults[2].append(dictData['total'])
            break
        else:
            changeAk(posResults)
            time.sleep(2)
    return posResults
    

#更换Ak
def changeAk(posResults):
    global lat #当前纬度
    global lng #当前经度
    global failTimes
    global ak
    global FaN
    global akQueue
    failTimes = failTimes - 1
    if failTimes == 0:
        if akQueue.qsize()>0:
            ak = akQueue.pop()
            failTimes = 100
        else :#已经没有ak可以用了,保存状态
            #保存状态
            saveProcejure()
            #把现在的数据存储起来
            saveInCsv(posResults,FaN)
            #给邮箱发邮件
            

#保存当前的状态
def saveProcejure():
    global maxLat,minLat,maxLng,minLng
    global cityList
    global oneCity
    global FaN
    global FList
    global lat #当前纬度
    global lng #当前经度
    #把当前城市插回去
    cityList.append(oneCity)
    #把当前设施插回去
    FList.append(FaN)
    saveInFile(','.join(cityList),'city')
    saveInFile(','.join(FList),'facility')
    #保存当前已遍历的点的状态
    str1 = str(maxLat)+','+str(minLat)+','+str(maxLng)+','+str(minLng)+'|'+str(lat)+','+str(lng)
    saveInFile(str1,'procejure')

#保存城市状态
def saveInFile(s,path):
    with open(gp.getPath(path), 'w') as f:
        f.write(s)
    

#过滤掉不合适的数据
#1以下的数据过滤
def judgeTotal(total):  
    if total<1:
        return False
    else:
        return True


#首先获取上次保留的状态
#return Range = (maxLat,minLat,maxLng,minLng),lastPos = (lat,lng)
def getProcedure():
    List = []
    Range = []
    lastPos = []
    with open(gp.getPath('procejure'),"r",encoding="UTF-8") as f:
        for line in f.readlines():
            List = line.split('|')

    Range = List[0].split(',')
    lastPos = List[1].split(',')
    return Range,lastPos


if __name__ == '__main__':
    try:
        #getFacilityNum() 
        getProcedure()
    except KeyboardInterrupt:  
        saveProcejure()

   






    

