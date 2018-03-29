import getDistrictData as dData #调用获取子级城市的模块
import urllib.parse
import json
import pandas as pd
import time
import sys

facilityInfoPath = 'facilityInfo/facilityInfo.txt'
ak = 'bc8jrgeAxrS2qMu5BUAGHIUHMpyAv3nj'


#获取某个项目的所有区
def get_PosData():
    for facility in get_facility():
        getUrl(facility)

def getUrl(facility):
    values={}
    totalpage = 0
    page_num = 0
    total_page = 0
    flag = 1
    results={}
    dList = dData.getdList()
    for oneCity in dList:
        results[oneCity] = []
        results[oneCity].append([])#经度
        results[oneCity].append([])#纬度
        results[oneCity].append([])#地址
        for oneDistrict in dList[oneCity] :
            values['query'] = facility
            values['region'] = oneCity + oneDistrict
            params = urllib.parse.urlencode(values)
            #先进行第一次获取总的页数
            url = 'http://api.map.baidu.com/place/v2/search?' + params + '&output=json&ak='+ ak +'&page_size=20&page_num=0'
            jsonData = dData.get_post_data(url)
            dictData = json.loads(jsonData)
            results = saveData(oneCity,results,dictData)
            total_page = dictData['total'] // 20
            #total_page = 5
            print(oneDistrict)

            #进行所有页数获取
            for i in range(0,total_page):
                page_num = page_num + 1
                url = 'http://api.map.baidu.com/place/v2/search?' + params + '&output=json&ak='+ ak +'&page_size=20&page_num=' + str(page_num)
                for waitCount in range(0,5):
                    jsonData = dData.get_post_data(url)
                    dictData = json.loads(jsonData)
                    if dictData['message'] == 'ok':
                        results = saveData(oneCity,results,dictData)
                        break
                    else:
                        print('sleep 5s')
                        time.sleep(5)

        saveInCsv(results,facility)

#超过并发量,等待后请求
def waitRequest(url,results,oneCity):
    for waitCount in range(0,5):
        jsonData = dData.get_post_data(url)
        dictData = json.loads(jsonData)
        if dictData['message'] == 'ok':
            results = saveData(oneCity,results,dictData)
            break
        else:
            print('sleep 5s')
            time.sleep(5)
    return results


#保存jsonData到字典
#return {'长沙':[[1,2,3,4,5],[2,3,5,6,7]]} [[经度],[纬度]]
def saveData(oneCity,results,dictData):
    try:
        re = dictData['results']
    except:
        print(dictData)
        re = dictData['result']
    else:  
        for r in re:
            results[oneCity][0].append(r['location']['lat'])
            results[oneCity][1].append(r['location']['lng'])
            try:
                results[oneCity][2].append(r['city'] + r['area'])
            except:
                results[oneCity][2].append(r['address'])
        return results

#保存到csv文件中
#facility 是设施名字
def saveInCsv(results,facility):
    for each in results:
        for pos in results[each]:
            dataframe = pd.DataFrame({'lat':results[each][0],'lng':results[each][1],'name':results[each][2]})
            dataframe.to_csv(each + '-' + facility + '.csv')

        
       
def get_facility():
    facilityName = []
    with open(facilityInfoPath,"r",encoding="UTF-8") as f:
        for line in f.readlines():
            facilityName = line.split()
    return facilityName

get_PosData()
