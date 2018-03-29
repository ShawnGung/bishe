import getParams as gp #调用获取子级城市的模块
import SMTP #调用获取子级城市的模块
import requests
import urllib.parse
import json
import pandas as pd
import datetime
import time
import math
import os
import sys
from queue import Queue


GDkey = gp.getGDkey()
disParam = gp.getDisParam()
time_start = 0
time_end  = 0
global failTimes
failTimes = 30
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
global posResults #当前结果集
global subject #用于传邮件提醒是否被终止了
posResults=[] #数量的Results
posResults.append([])#纬度
posResults.append([])#经度
posResults.append([])#数量



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
    url = 'http://restapi.amap.com/v3/config/district?key=' + GDkey + '&' + params + '&output=json&subdistrict=2'
    jsonData = get_post_data(url)
    data = json.loads(jsonData)
    for each in data['districts'][0]['districts']:
        for eachDis in each['districts']:
            lng,lat = eachDis['center'].split(',')
            latList.append(gp.str2float(lat))
            lngList.append(gp.str2float(lng))
    return round(max(latList),3),round(min(latList),3),round(max(lngList),3),round(min(lngList),3)


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
    procejureFlag = False #新的抓取
    Range,lastPos = getProcedure()
    
    #设置中断补抓的标志
    if len(Range)>0 and len(lastPos)>0 :
        procejureFlag = True

    global posResults #当前结果集
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
        if procejureFlag == False:
            maxLat,minLat,maxLng,minLng = getRange(oneCity)
        else :
            maxLat,minLat,maxLng,minLng = Range
        latRange = int((maxLat-minLat) // disParam)
        lngRange = int((maxLng-minLng) // disParam)

        #正常的流程（从开头捕捉）
        if procejureFlag == False:
            for i in range(0,latRange+1):
                for j in range(0,lngRange+1):
                    searchPoint(i,j)
        else:
            conI = math.ceil((lastPos[0] - minLat) / disParam) 
            conJ = math.ceil((lastPos[1] - minLng) / disParam)
            # 第一次把经度的补上
            LngFlag = True
            if conJ+1 <= lngRange : #边界控制
                for i in range(conI,latRange+1): #当前点作为已爬取点
                    if LngFlag == True: #先遍历剩下经度
                        for j in range(conJ+1,lngRange+1):
                            searchPoint(i,j)
                        #剩下经度遍历完了，再重新遍历
                        LngFlag = False
                    else: 
                        for j in range(0,lngRange+1):
                            searchPoint(i,j)
            else:#超出边界，纬度递增
                for i in range(conI+1,latRange+1): #当前点作为已爬取点
                    for j in range(0,lngRange+1):
                        searchPoint(i,j)
            procejureFlag = False #当前城市已经爬取完,重置为重新抓取


#遍历每个点
def searchPoint(i,j):
    global posResults #当前结果集
    global maxLat,minLat,maxLng,minLng
    global FaN #当前设备名称
    global lat #当前纬度
    global lng #当前经度
    global ak
    values={}
    lat = round(i*disParam + minLat,3)
    lng = round(j*disParam + minLng,3)
    values['query'] = FaN
    params = urllib.parse.urlencode(values)
    #url = 'http://api.map.baidu.com/place/v2/search?'+ params+'&location='+str(lat)+','+str(lng)+\
     #       '&radius=' + str(gp.getMetParam()) + '&output=json&ak='+ ak +'&page_size=20&page_num=0'
    url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+str(lat)+','+str(lng)+'&types='+ gp.bankCode +'&radius='+str(gp.getMetParam())\
    +'&offset=20&page=1&extensions=base'
    posResults = waitRequest(url)
    print((lat,lng))
    if j % 100 == 0 and j!=0:#每100次存储一次数据
        saveInCsv(posResults,FaN)




#保存到csv文件中 
#facility 是设施名字
def saveInCsv(results,facility):
    oriData = loadFromCsv()
    #转换为dataframe
    reDataFrame = pd.DataFrame({'lat':results[0],'lng':results[1],'bank':results[2]})
    #合并
    finData = oriData.append(reDataFrame)
    finData.to_csv(facility + '.csv',index=False)
    dictReset(results)
    print('saved')
    print('目前有'+str(len(finData))+'条数据')


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
def waitRequest(url):
    global lat #当前纬度
    global lng #当前经度
    global posResults #当前结果集
    global failTimes
    while True:
        jsonData = get_post_data(url)
        dictData = json.loads(jsonData)
        #if dictData['message'] == 'ok' and dictData['status'] == 0:
        if dictData['infocode'] == '10000':
            failTimes = 30 #成功一次后重新刷新，如果连续100次都失败，更换ak
            #if judgeTotal(dictData['total']):
            if judgeTotal(int(dictData['count'])):
                posResults[0].append(lat)
                posResults[1].append(lng)
                #posResults[2].append(dictData['total'])
                posResults[2].append(dictData['count'])
            break
        elif dictData['infocode'] == '10003':
            failTimes = 0
            url = changeAk(posResults,url)
        else:
            failTimes = failTimes -1
            url = changeAk(posResults,url)
            time.sleep(1)
    return posResults
    

#更换Ak
def changeAk(posResults,url):
    global lat #当前纬度
    global lng #当前经度
    global failTimes
    global ak
    global FaN
    global akQueue
    if failTimes == 0:
        if akQueue.qsize()>0:
            if akQueue.qsize()%10 == 0:
                SMTP.send('更换ak,剩余:'+str(akQueue.qsize()))
            oldAK = ak
            ak = akQueue.get()
            failTimes = 30
            #更新当前url
            url = url.replace(oldAK,ak)
            return url
        else :#已经没有ak可以用了,保存状态
            #保存状态
            SMTP.send('ak用完')
            saveProcejure()
            os._exit(0)
    else:#返回原来的url
        return url
            

#保存当前的状态
def saveProcejure():
    global maxLat,minLat,maxLng,minLng
    global cityList
    global oneCity
    global FaN
    global FList
    global lat #当前纬度
    global lng #当前经度
    global posResults #当前结果集
    #把当前城市插回去
    cityList.append(oneCity)
    #把当前设施插回去
    FList.append(FaN)
    saveInFile(','.join(cityList),'city')
    saveInFile(','.join(FList),'facility')
    #保存当前已遍历的点的状态
    str1 = str(maxLat)+','+str(minLat)+','+str(maxLng)+','+str(minLng)+'|'+str(lat)+','+str(lng)
    saveInFile(str1,'procejure')
    #把现在的数据存储起来
    saveInCsv(posResults,FaN)
    #进行邮件的提醒
    content = getContent()
    SMTP.send(content)
    

#构造邮件信息
def getContent():
    global cityList
    global oneCity
    global FaN
    global FList
    #目前多少条数据
    oriData = loadFromCsv()
    dataNum ='目前有'+str(len(oriData))+'条数据'
    #剩下城市
    strCity = '剩下城市:'+','.join(cityList)
    #剩下设施
    strFac = '剩下设施:'+','.join(FList)
    #目前遍历到哪个点
    Range,lastPos = getProcedure()
    strPro = '('+str(Range[1])+','+str(Range[0])+'),'+'('+str(Range[3])+','+str(Range[2])+')'
    strPro = '范围:'+strPro + '\n当前遍历点:(' +str(lastPos[0])+','+str(lastPos[1])+')'
    #日志情况
    log = '日志情况:'+str(readLog())
    content = dataNum+'\n'+strCity+'\n'+strPro+'\n'+strFac+'\n'+log
    return content

#保存城市状态
def saveInFile(s,path):
    with open(gp.getPath(path), 'w') as f:
        f.write(s)
    

#过滤掉不合适的数据
#5以下的数据过滤
def judgeTotal(total):  
    if total<0:
        return False
    else:
        return True


#首先获取上次保留的状态
#return Range = (maxLat,minLat,maxLng,minLng),lastPos = (lat,lng)
def getProcedure():
    List = []
    strRange = []
    strlastPos = []
    floatRange = []
    floatlastPos = []
    List = getProcejureDetail(gp.getPath('procejure'))

    if len(List) == 0 :#如果是空，直接返回
        return floatRange,floatlastPos 


    strRange = List[0].split(',')
    strlastPos = List[1].split(',')
    for each in strRange:
        floatRange.append(gp.str2float(each))
        
    for each in strlastPos:
        floatlastPos.append(gp.str2float(each))
    
    return floatRange,floatlastPos

#判断文件存在
def getProcejureDetail(path):
    List = []
    if os.path.isfile(path): #如果不存在就返回False 
        with open(path,"r",encoding="UTF-8") as f:
            for line in f.readlines():
                List = line.split('|')
            return List
    else:
        with open(path,"w",encoding="UTF-8") as f:
            return List

#读取日志
def readLog():
    with open('exception.log', 'r') as f:
         text = f.read()
         return text

#保存日志
def saveInLog(e):
    with open('exception.log', 'a') as f:
        nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
        content = nowTime+'\n'+e+'\n'
        f.write(content)


#清空文件内容
def clearFile():
    with open(gp.getPath('city'),"w",encoding="UTF-8") as f:
        f.write("")
    with open(gp.getPath('facility'),"w",encoding="UTF-8") as f:
        f.write("")
    with open(gp.getPath('procejure'),"w",encoding="UTF-8") as f:
        f.write("")

#循环重启
def main():
    try:
        getFacilityNum()
        #数据清空
        clearFile()
        print('抓取完成')
        #getProcedure()
    except KeyboardInterrupt:
        print("ctr+c中断并且保存状态和数据")
        saveProcejure()
    except requests.exceptions.ConnectionError as e:     
        saveProcejure()
        print(e)
        print('保存状态，重启')
        main()
    except BaseException as e:
        print('出现未知错误')
        print(e)
        saveInLog(str(e))
        SMTP.send('程序被终止了')
        saveProcejure()
        
if __name__ == '__main__':
    main()

    #print(getRange('北京市'))
    #print(gp.getCityList())




    

