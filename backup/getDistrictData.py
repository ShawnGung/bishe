import requests
import urllib.parse
import json

key = 'e053d41d5e06ae71ab79dca226e5f6e2'
cityInfoPath = 'cityInfo/cityInfo.txt'

def get_post_data(url):
    # 首先获取到登录界面的html
    r = requests.get(url)
    return r.text

#获取查询的城市集合
#return array
def get_city_name():
    cityName = []
    with open(cityInfoPath,"r",encoding="UTF-8") as f:
        for line in f.readlines():
            cityName = line.split()
    return cityName


#获取下一级县区的集合
def get_next_district(cityName):
    dList = {};
    for oneCity in cityName:
        dList[oneCity] = []
        params = get_urlencode_params(oneCity)
        url = 'http://restapi.amap.com/v3/config/district?key=' + key + '&' + params + '&output=json'
        jsonData = get_post_data(url)
        data = json.loads(jsonData)
        districts = data['districts'][0]['districts']
        for d in districts :
            dList[oneCity].append([])
            dList[oneCity][-1] = d['name']
    return dList


def get_urlencode_params(oneCity):
    values={}
    values['keywords'] = oneCity
    params=urllib.parse.urlencode(values)
    return params


#获取所有县级级别的集合
def getdList():
    cityName = get_city_name()
    dList = get_next_district(cityName)
    return dList


if __name__ == '__main__':
    dList = getdList();
    print(dList)
