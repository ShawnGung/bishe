#最终的输入接口
import ml
import getParams as gp #调用获取子级城市的模块
import getLeftPos as glp
import requests
import urllib.parse
import sys
import math
import os
import getPosData as gpd
import json
import gc

KNNnum = ml.KNNnum

global codeDict
global ak
import SMTP
global akQueue
akQueue = gp.getAkQueue()#ak的队列
ak = akQueue.get()
codeDict = gp.getCodeDict()
disParam = 0.02
#定义一个大约2000-4000米的半径参数
disLatParamRate = 1
disLngParamRate = 1.3
#分档参数
type4 = 0.5
type3 = 0.4
type2 = 0.3
type1 = 0.2
type0 = 0.1


#=====================RESTFUL API=================


#获取某个城市的中心坐标
def getCityCenter(cityName):
    global ak
    url = 'http://restapi.amap.com/v3/config/district?key=' + ak + '&keywords=' + cityName + '&output=json&subdistrict=0&extensions=base'
    jsonData = gpd.get_post_data(url)
    jsonData = json.loads(jsonData)
    lng,lat = jsonData['districts'][0]['center'].split(',')
    result = {}
    result['lng'] = lng
    result['lat'] = lat
    return json.dumps(result)


#============================================================

#预先抓取完所有的内容并且保存起来,用于Echarts
#返回一个list
#task 用于更新进度条
def getCityKNNData(cityName,facType,task = ''):
    path = cityName +'-'+facType+'.json'
    pathTmp = cityName +'-'+facType+'Tmp.json'
    if os.path.isfile('Echarts/'+path): #如果不存在就返回False 
        with open('Echarts/'+path,"r",encoding="UTF-8") as f:
            for line in f.readlines():
                List = json.loads(line)
            return List
    else:
        List = []
        coordinateList = []
        maxLat,minLat,maxLng,minLng = gpd.getRange(cityName)
        #算出格子的大小
        cellRow = int((maxLat-minLat) // (disParam*disLatParamRate))
        cellCol = int((maxLng-minLng) // (disParam*disLngParamRate))
        print((cellRow,cellCol))
        i = 0
        for row in range(cellRow):
            for col in range(cellCol):
                i = i + 1
                if task != '':
                    percent = i/(cellRow*cellCol)
                    percent = round(percent,3)
                    percent = ' percent: {:.2%}'.format(percent)
                    task.update_state(state='PROGRESS',meta={'percent':percent})
                coordinate = []
                clat = round(row*disParam*disLatParamRate+minLat,3)
                clng = round(col*disParam*disLngParamRate+minLng,3)
                coordinate.append(str(clat))
                coordinate.append(str(clng))
                #diff,result = getKNNFinal(coordinate,facType) 第一个版本
                diff,result = getKNNFinalByOri(coordinate,facType)
                print('('+str(clat)+','+str(clng)+')')
                content = '('+str(clat)+','+str(clng)+')-('+str(diff)+')'
                saveInLog(content)
                List.append({'lng':clng,'lat':clat,'diff':diff,'result':result})
                del diff
                del result

                load_dict = []
                if i%50 == 0 or((row == cellRow-1)and(col == cellCol -1)):#每当存满50个进行存到文件并且释放List
                    print(os.path.isfile('Echarts/'+pathTmp))
                    if os.path.isfile('Echarts/'+pathTmp):#如果不存在
                        with open('Echarts/'+pathTmp,"r") as f:
                            load_dict = json.load(f)
                            load_dict.extend(List)
                    else:
                        load_dict = List
                    with open('Echarts/'+pathTmp,"w",encoding="UTF-8") as f:
                        f.write(json.dumps(load_dict))
                    List.clear()
                    del List
                    List = []
                    load_dict.clear()
                    del load_dict
            gc.collect()
        #当搜索完了,我们需要把文件名梗概
        os.rename('Echarts/'+pathTmp, 'Echarts/'+path)            
       
        print(cityName +'-'+facType+'的Echarts数据已完成')

#=========================第二个版本=========================================
#获取KNN所需要的csv格式
#ByOri指第二个版本，不采用用来的先分5类，而是根据比例来分
def getKNNDataByOri(facType):
    ori = ml.reshapeCsv()
    leftSampleList,leftLabelList = ml.getCsvIndex(facType)
    temp = []
    temp.append(facType)
    leftLabelList =temp #直接取原来的数值
    copySam = ori.loc[:,leftSampleList].copy()
    copyRe = ori.loc[:,leftLabelList].copy()
    del leftSampleList
    del leftLabelList
    return copySam,copyRe


#获取KNN的预测结果以及原来的结果
#ByOri指第二个版本，不采用用来的先分5类，而是根据比例来分
#coordinate,facType(bank)
def getKNNByOri(coordinate,facType):
    oriCount,sample = getKNNsampleByOri(coordinate,facType)
    content = "sample:"+str(sample)
    saveInLog(content)
    dataSet,labels = getKNNDataByOri(facType)
    sampleResult,labelsResult = ml.getKNN(facType,sample,dataSet,labels,KNNnum)
    del dataSet
    del labels
    return oriCount,labelsResult


#获取KNN的sample数据,通过经纬度，获取其余别的特征的数据，返回一个列表
#返回预测特征的原始数据，以及其余特征的数据列表
def getKNNsampleByOri(coordinate,facType):
    global codeDict
    global ak
    leftFacEng,leftFacChi = ml.getleftFac()
    leftFacEng.remove(facType)#删除要搜索的type,然后搜索sample
    sample = []

    url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+coordinate[0]+','+coordinate[1]+'&types='+ codeDict[facType] +'&radius='+str(gp.getMetParam())\
            +'&offset=20&page=1&extensions=base'
    count = waitRequest(url)

    for each in leftFacEng:
        url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+coordinate[0]+','+coordinate[1]+'&types='+ codeDict[each] +'&radius='+str(gp.getMetParam())\
              +'&offset=20&page=1&extensions=base'
        sample.append(waitRequest(url))
    return count,sample


#根据预测结果以及原来的结果,给出判断
#ByOri指第二个版本，不采用用来的先分5类，而是根据比例来分
#返回两个值,9个档次 +　缺少多少个
def getKNNFinalByOri(coordinate,facType):
    oriCount,labelsResult = getKNNByOri(coordinate,facType)
    processedResult = getAvgResult(labelsResult)
    result = ''
    bigResult = ''
    #分档参数
    range4 = type4*processedResult #>50%
    range3 = type3*processedResult #>40%
    range2 = type2*processedResult #>30%
    range1 = type1*processedResult #>20%
    mrange4 = -type4*processedResult #<-50%
    mrange3 = -type3*processedResult #<-40%
    mrange2 = -type2*processedResult #<-30%
    mrange1 = -type1*processedResult #<-20%
    content = "原来数据:"+str(oriCount)+',预测数据:'+str(processedResult)+',[KNN列表]:'+str(labelsResult)
    saveInLog(content)

    #特殊情况处理,如果是银行的话，需要进行样本不存在的特殊情况处理
    #if (oriCount == 0 or oriCount == 1) and labelsResult[0] == 2:
    #    result = 0
    #    bigResult = 2
    #    return result,bigResult
    

    #差值
    diff = oriCount - processedResult

    #如果是差值0的话,直接相同（处理oriCount和预测cont都是0的情况）
    if diff == 0 :
        result = 0
        bigResult = 2
        return result,diff

    #如果labelsResult中有多于5个0.0的出现,直接返回0
    if labelsResult.count(0) >=5 :
        result = 0
        bigResult = 2
        return result,diff

    #processResult预测值如果低于10的话,3个以内都为0
    if processedResult >= 0 and processedResult <= 9 :
        if diff >= 7 : #>7
            result = 4
            bigResult = 3
        elif diff >= 6 and diff < 7 : # (6,7)
            result = 3
            bigResult = 3
        elif diff >= 5 and diff < 6 : # (5,6)
            result = 2
            bigResult = 3
        elif diff >= 4 and diff < 5 : # (4,5)
            result = 1
            bigResult = 2                
        elif diff >= -4 and diff < 4 : # (-4,4)
            result = 0
            bigResult = 2
        elif diff >= -5 and diff < -4 : # (-5,-4)
            result = -1
            bigResult = 2
        elif diff >= -6 and diff < -5 : # (-6,-5)
            result = -2
            bigResult = 1
        elif diff >= -7 and diff < -6 : # (-7,-6)
            result = -3
            bigResult = 1
        elif diff <= -7: # <-7
            result = -4
            bigResult = 1
            
        return result,diff

    #processedResult预测值高于10的进行下面
    #4档,超饱和
    if diff >= range4: #>50%
        result = 4
        bigResult = 3
    elif diff<range4 and diff >= range3: # 40%-50% 中等饱和
        result = 3
        bigResult = 3
    elif diff<range3 and diff >= range2: # 30%-40%
        result = 2
        bigResult = 3
    elif diff<range2 and diff >= range1: # 20%-30%
        result = 1
        bigResult = 2
    elif diff<range1 and diff >= mrange1: # -20%-20%
        result = 0
        bigResult = 2
    elif diff<mrange1 and diff >= mrange2: # -30% - -20%
        result = -1
        bigResult = 2
    elif diff<mrange2 and diff >= mrange3: # -40% - -30%
        result = -2
        bigResult = 1
    elif diff<mrange3 and diff >= mrange4: # -40% - -50%
        result = -3
        bigResult = 1
    elif diff<mrange4: # <50%
        result = -4
        bigResult = 1
    return result,diff



#去掉最小最大值，然后求平均值
def getAvgResult(labelsResult):
    temp = labelsResult[1:] #第一个不取
    minOne = min(temp)
    maxOne = max(temp)
    temp.remove(minOne)
    temp.remove(maxOne)
    temp.insert(0,labelsResult[0]) #把第一个值插回去
    #只取前四个平均值
    avg = temp[0]*0.4+temp[1]*0.3+temp[2]*0.2+temp[3]*0.1
    return avg
    



#=============================第一个版本=====================================


#获取KNN所需要的csv格式
def getKNNData(facType):
    ori = ml.reshapeCsv()
    leftSampleList,leftLabelList = ml.getCsvIndex(facType)
    copySam = ori.loc[:,leftSampleList].copy()
    copyRe = ori.loc[:,leftLabelList].copy()
    return copySam,copyRe


#获取KNN的预测结果以及原来的结果
#coordinate,facType(bank)
def getKNN(coordinate,facType):
    oriType,sample = getKNNsample(coordinate,facType)
    dataSet,labels = getKNNData(facType)
    sampleResult,labelsResult = ml.getKNN(facType,sample,dataSet,labels,KNNnum)
    return oriType,max(labelsResult,key = labelsResult.count)


#根据预测结果以及原来的结果,给出判断
#返回两个值,差值与结果值（1,2,3）分别代表不饱和，刚好，饱和
def getKNNFinal(coordinate,facType):
    oriType,finalType = getKNN(coordinate,facType)
    diff = int(finalType[4]) - int(oriType[4])
    result = ''
    if diff in range(2,5):
        result = 3
    elif diff in [-1,0,1]:
        result = 2
    elif diff in [-2,-3,-4]:
        result = 1
    return diff,result
    


#获取KNN的sample数据,通过经纬度，获取其余别的特征的数据，返回一个列表
def getKNNsample(coordinate,facType):
    global codeDict
    global ak
    leftFacEng,leftFacChi = ml.getleftFac()
    leftFacEng.remove(facType)#删除要搜索的type,然后搜索sample
    sample = []
    oriType = getOriType(coordinate,facType)

    for each in leftFacEng:
        url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+coordinate[0]+','+coordinate[1]+'&types='+ codeDict[each] +'&radius='+str(gp.getMetParam())\
              +'&offset=20&page=1&extensions=base'
        sample.append(waitRequest(url))
    return oriType,sample


#根据数量获取API中的数量
def getOriType(coordinate,facType):
    global codeDict
    global ak
    url = 'http://restapi.amap.com/v3/place/around?key='+ ak +'&location='+coordinate[0]+','+coordinate[1]+'&types='+ codeDict[facType] +'&radius='+str(gp.getMetParam())\
              +'&offset=20&page=1&extensions=base'
    count = waitRequest(url)

    csv = glp.getFinalCsv()
    copy = csv.copy()
    
    typeName = copy[facType]
    t1 = int(typeName.quantile(1/5))
    t2 = int(typeName.quantile(2/5))
    t3 = int(typeName.quantile(3/5))
    t4 = int(typeName.quantile(4/5))
    t5 = int(typeName.quantile(5/5))
    
    if count in range(0,t1+1):
        return 'type1'
    elif count in range(t1+1,t2+1):
        return 'type2'
    elif count in range(t2+1,t3+1):
        return 'type3'
    elif count in range(t3+1,t4+1): 
        return 'type4'
    elif count in range(t4+1,t5+1):
        return 'type5'
    


#请求
def waitRequest(url):
    while True:
        try:
            jsonData = gpd.get_post_data(url)
            dictData = json.loads(jsonData)
            if dictData['infocode'] == '10000':
                return int(dictData['count'])
            elif dictData['infocode'] == '10003':
                url = changeAk(url)
        except requests.exceptions.ConnectionError as e:
            print(e)
            waitRequest(url)
            
#更换Ak
def changeAk(url):
    global ak
    global akQueue
    if akQueue.qsize()>0:
        oldAK = ak
        ak = akQueue.get()
        print('ak还剩下:'+str(akQueue.qsize()))
        #更新当前url
        url = url.replace(oldAK,ak)
        return url
    else :#已经没有ak可以用了,保存状态
        #保存状态
        SMTP.send('ak用完')
        os._exit(0)

#保存输出日志
def saveInLog(content):
    try:
        with open('finalInterface/finalInterface.log', 'a') as f:
            f.write(content+'\n')
    except BaseException as e:
        print(e)
        saveInLog(content)
        


if __name__ == '__main__':
    #diff,re = getKNNFinal(['24.485','110.397'],'bank')
    try:
        getCityKNNData('成都市','bank')
        #getCityCenter('北京市')
    except KeyboardInterrupt:
        print("ctr+c中断")
        os._exit(0)
    except BaseException as e:
        print('出现未知错误')
        print(e)
