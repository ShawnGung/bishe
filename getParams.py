from functools import reduce

from queue import Queue
#获取所需的参数
akListPath = 'akList.txt'
cityListPath = 'cityList.txt'
facilityInfoPath = 'facilityInfo.txt'
procejureInfoPath = 'procejureInfo.txt'
leftFacilityInfoPath = 'leftFacility.txt'
finalCsvInfoPath = 'finalCsv.csv'
poiCideInfoPath = 'POI.txt'
firstColEng = 'bank'
firstColChi = '银行'
bankCode = '160100'



#初始化codeDict
def getCodeDict():
    List = []
    Dict = {}
    with open(poiCideInfoPath,"r",encoding="UTF-8") as f:
        for line in f.readlines():
            List = line.split('|')
        
    name,code = List[0].split(','),List[1].split(',')
    for i in range (len(name)):
        Dict[name[i]] = code[i]
    return Dict


    
#返回路径
def getPath(name):
    if name == 'city':
        return cityListPath
    elif name == 'facility':
        return facilityInfoPath
    elif name == 'procejure':
        return procejureInfoPath
    elif name == 'leftfacility':
        return leftFacilityInfoPath
    elif name == 'finalCsv':
        return finalCsvInfoPath

#获取剩余的设施
def get_leftFacility():
    with open(leftFacilityInfoPath,"r",encoding="UTF-8") as f:
        for line in f.readlines():
            List = line.split('|')
    return List[0].split(','),List[1].split(',')



#获取爬虫的所需参数（ak和城市）
def getList(Path):
    List = []
    try:
        with open(Path,"r",encoding="gbk") as f:
            for line in f.readlines():
                List = line.split(',')
    except:
        with open(Path,"r",encoding="UTF-8") as f:
            for line in f.readlines():
                List = line.split(',')
    return List

def get_facility():
    facilityName = []
    try:
        with open(facilityInfoPath,"r",encoding="gbk") as f:
            for line in f.readlines():
                facilityName = line.split(',')
    except:
        with open(facilityInfoPath,"r",encoding="UTF-8") as f:
            for line in f.readlines():
                facilityName = line.split(',')
    return facilityName

#获取akList
def getAkList():
    return getList(akListPath)


#获取akList
def getCityList():
    return getList(cityListPath)


#返回高德地图的key
def getGDkey():
    return 'b956e1872175b38349a82fe8cded30d2'

#按照0.02的递增来进行遍历,粗粒度地遍历
def getDisParam():
    return 0.015

#按照2000米的递增来进行遍历,粗粒度地遍历
def getMetParam():
    return 2000


def str2float(s):  
    def char2num(s):  
        return {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}[s]  
    n = s.index('.')  
    return reduce(lambda x,y:x*10+y,map(char2num,s[:n]+s[n+1:]))/(10**(len(s) - n - 1))  

#构建ak队列
def getAkQueue():
    akQueue = Queue()
    akList = getAkList()
    for each in akList:
        akQueue.put(each)
    return akQueue

if __name__ == '__main__':
   dic = getCodeDict()
