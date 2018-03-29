import requests
import urllib.parse
import json
import sys
from functools import reduce

GDkey = 'b956e1872175b38349a82fe8cded30d2'

def str2float(s):  
    def char2num(s):  
        return {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}[s]  
    n = s.index('.')  
    return reduce(lambda x,y:x*10+y,map(char2num,s[:n]+s[n+1:]))/(10**(len(s) - n - 1))  



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
    url = 'http://restapi.amap.com/v3/config/district?key=' + GDkey + '&keywords=' + oneCity + '&output=json&subdistrict=2'
    jsonData = get_post_data(url)
    data = json.loads(jsonData)
    for each in data['districts'][0]['districts']:
        for eachDis in each['districts']:
            lng,lat = eachDis['center'].split(',')
            latList.append(lat)
            lngList.append(lng)
    return round(str2float(max(latList)),3),round(str2float(min(latList)),3),round(str2float(max(lngList)),3),round(str2float(min(lngList)),3)


if __name__ == '__main__':
    #print(sys.argv[1])
    print(getRange('北京市'))
