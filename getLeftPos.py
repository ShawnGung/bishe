import pandas as pd
import getParams as gp #调用获取子级城市的模块
import numpy as np
import SMTP
import os
import time
import json
import getPosData as gpd

import requests
import urllib.parse
import sys



global FaN
global leftFacEng
global leftFacChi
global oriCsv
global codeDict
global akQueue
akQueue = gp.getAkQueue()#ak的队列
global ak
ak = akQueue.get()
FaN = '银行'
codeDict = gp.getCodeDict()
finalFile = 'total.csv'




#首先读取原来的csv
def getExistsPos():
    try:
        global FaN
        f=open(FaN+'.csv') #解决pandas读取中文名的文件名问题
        data = pd.read_csv(f,encoding='utf-8') #解决编码问题utf-8
        return data
    except:
        return pd.DataFrame()


#获取剩余的设施数据
def getleftFac():
    global leftFacEng
    global leftFacChi
    leftFacEng,leftFacChi = gp.get_leftFacility()

#获取最终文件的csv
def getFinalCsv():
    finalCsv = []
    csvPath = gp.getPath('finalCsv')
    if os.path.isfile(csvPath): #如果不存在就返回False
        f=open(gp.getPath('finalCsv')) #解决pandas读取中文名的文件名问题
        try:
            finalCsv = pd.read_csv(f,encoding='utf-8') #解决编码问题utf-8
        except:#如果为空的话
            return pd.DataFrame({})
    else:
        finalCsv = pd.DataFrame({})
        with open(csvPath,"w",encoding="UTF-8") as f:
            pass
        finalCsv.to_csv(csvPath,index=False)
    return finalCsv


#调整最终csv的行数至一致
def adjustSize():
    finalDict={}
    global oriCsv
    oriCsv = getExistsPos()
    finalCsv = getFinalCsv()
    dis =len(oriCsv) - len(finalCsv)#两个csv相差的行数
    if dis != 0 : #如果第一列银行数总数没变，那就调整完毕
        if len(finalCsv.keys()) == 0: #如果本身文件就是空
            newList = oriCsv[gp.firstColEng].tolist()
            finalDict[gp.firstColEng] = newList
            finalCsv = pd.DataFrame(finalDict)
            finalCsv.to_csv(gp.getPath('finalCsv'),index=False)#空值用NAN代表
        else:
            for listName in finalCsv.keys():
                if len(finalCsv[listName]) != 0:
                    if listName != gp.firstColEng :#如果这列不是银行才补充None
                        newList = finalCsv[listName].tolist()
                        newList.extend([None]*dis)#相同行数的某个list
                    else:#如果是银行
                        newList = oriCsv[gp.firstColEng].tolist()
                else:
                    newList = [None]*dis
                finalDict[listName] = newList
            #转换dataframe
            finalCsv = pd.DataFrame(finalDict)
            finalCsv.to_csv(gp.getPath('finalCsv'),index=False,na_rep='NaN')#空值用NAN代表

#进行遍历
#目前的finalCsv,行数是满的，bank的是已完成的
def search():
    global leftFacEng
    global leftFacChi
    global oriCsv
    global codeDict
    global ak
    i = -1
    finalCsv = getFinalCsv()
    for each in leftFacEng:
        i = i + 1
        #首先判断有否这个列
        if each not in finalCsv.keys():
            newList = [np.nan]*len(finalCsv)
            finalCsv[each] = newList
        for point,eachLat,eachLng in zip(range(0,len(oriCsv)),oriCsv['lat'],oriCsv['lng']):    
            if pd.isnull(finalCsv[each][point]): #如果这个是空的才进行遍历
                values={}
                values['query'] = leftFacChi[i]
                params = urllib.parse.urlencode(values)
                #url = 'http://api.map.baidu.com/place/v2/search?'+ params+'&location='+str(eachLat)+','+str(eachLng)+\
                #       '&radius=' + str(gp.getMetParam()) + '&output=json&ak='+ ak +'&page_size=20&page_num=0'
                url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+str(eachLat)+','+str(eachLng)+'&types='+ codeDict[each] +'&radius='+str(gp.getMetParam())\
                +'&offset=20&page=1&extensions=base'
                #print(url)
                print(str(eachLat)+','+str(eachLng))
                waitRequest(url,finalCsv,each,point)
                if point%100 == 0 and point!=0 or point == len(oriCsv)-1:
                    saveInCsv(finalCsv,each,point)


#保存到csv文件中
def saveInCsv(finalCsv,each,point):
    finalDataFrame = pd.DataFrame(finalCsv)
    finalDataFrame.to_csv(gp.getPath('finalCsv'),index=False)
    print('当前'+each+'搜索到了'+str(point)+'条数据')


#请求
def waitRequest(url,finalCsv,each,point):
    failTimes = 30
    while True:
        start = time.clock()
        jsonData = gpd.get_post_data(url)
        dictData = json.loads(jsonData)
        #if dictData['message'] == 'ok' and dictData['status'] == 0:
        if dictData['infocode'] == '10000':
            failTimes = 30 #成功一次后重新刷新，如果连续100次都失败，更换ak
            finalCsv[each][point] = dictData['count']
            break
        elif dictData['infocode'] == '10003':
            failTimes = 0
            url = changeAk(url,failTimes)
        else:
            failTimes = failTimes - 1
            url = changeAk(url,failTimes)
            time.sleep(1)

#更换Ak
def changeAk(url,failTimes):
    global ak
    global akQueue
    if failTimes == 0:
        if akQueue.qsize()>0:
            if akQueue.qsize()%10 == 0:
                SMTP.send('更换ak')
            oldAK = ak
            ak = akQueue.get()
            #更新当前url
            url = url.replace(oldAK,ak)
            return url
        else :#已经没有ak可以用了,保存状态
            #保存状态
            SMTP.send('ak用完')
            os._exit(0)
    else:#返回原来的url
        return url


#出错之后再循环
def main():
    try:
        getleftFac()
        adjustSize()
        #csv = getFinalCsv()
        search()
    except:
        main()


if __name__ == '__main__':
    getleftFac()
    adjustSize()
    #csv = getFinalCsv()
    search()
