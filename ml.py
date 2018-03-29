import sys
import getLeftPos as glp
import getParams as gp #调用获取子级城市的模块
import numpy as np
import random
import os

KNNnum = 10
predicNum = 40
typeNum=5 #每个类别分成了5类
typeList = ['type1','type2','type3','type4','type5']
global random20List
random20List = []
global i,j,k,l


#获取Bayes的数据集
def getBayesData():
    #getrandom20List()
    ori = reshapeCsv();
    leftList = getleftList()
    indexList = getBayesIndex()
    re = ori.loc[leftList,indexList].copy()
    return re



#获取对应需要的index进行部分csv选取
#leftLabelList就是对应的标签名字,bankType
def getBayesIndex():
    csv = glp.getFinalCsv()
    oriIndex = csv.keys()
    newIndex = []
    for each in oriIndex:
        newIndex.append(each+'Type')
    return newIndex


#得到预测值
#sample 就是一行按index顺序的list(bank,hospital,house,school,supermarket),四个值
#predictType 就是预测哪个值 (bankType)
def getBayesPredict(sample,predictType):               
    csvData = getBayesData()
    csvDataSize = len(csvData)#csvData的长度
    pList = {}
    #首先获取P(type)
    for eachType in typeList:
        eachTypeCsv = csvData[csvData[predictType] == eachType]
        eachTypeSize = len(eachTypeCsv)
        Ptype = eachTypeSize / csvDataSize
        indexList = getBayesIndex()
        indexList.remove(predictType)
        try:
            #第一个特征值
            c1Csv = eachTypeCsv[eachTypeCsv[indexList[0]] == sample[0]]
            c1Size = len(c1Csv)
            Pc1 = c1Size / eachTypeSize
            #第二个特征值
            c2Csv = eachTypeCsv[eachTypeCsv[indexList[1]] == sample[1]]
            c2Size = len(c2Csv)
            Pc2 = c2Size / eachTypeSize        
            #第三个特征值
            c3Csv = eachTypeCsv[eachTypeCsv[indexList[2]] == sample[2]]
            c3Size = len(c3Csv)
            Pc3 = c3Size / eachTypeSize
            #第四个特征值
            c4Csv = eachTypeCsv[eachTypeCsv[indexList[3]] == sample[3]]
            c4Size = len(c4Csv)
            Pc4 = c4Size / eachTypeSize
            bayesResult = Pc1*Pc2*Pc3*Pc4*Ptype
            pList[eachType] = bayesResult
        except:
            pList[eachType] = 0
    predictResult = max(pList, key=pList.get)
    return predictResult


#获取交叉验证的百分比
def getBayesPercent():
    indexs = getBayesIndex()#bankType,houseType....
    indexsCopy = indexs.copy()
    for each in indexs:
        bayesPercentList = []
        for i in range(20):
            getrandom20List()
            ori = reshapeCsv()
            indexsCopy = indexs.copy()
            indexsCopy.remove(each)
            leftSample = ori.loc[random20List,indexsCopy]
            testSample = ori.loc[random20List,each]
            count = 0
            for index in testSample.index:
                sampleList = leftSample.loc[index].tolist()
                predictResult = getBayesPredict(sampleList,each)
                if predictResult == testSample[index]:
                    count = count+1
            print(' percent: {:.2%}'.format(count/predicNum))
            bayesPercentList.append(count/predicNum)
        content = each+' percent: {:.2%}'.format(sum(bayesPercentList)/len(bayesPercentList))
        saveInFile(content+'\n',r'bayesPercent'+os.path.sep+'bayesPercent.txt')
        print(each+'获取完')


#随机抽取predicNum条样本数据
def getrandom20List():
    global random20List
    random20List.clear()
    csvSize = len(glp.getFinalCsv())
    for i in range(0,predicNum):
        r = random.randint(0,csvSize)
        if r in random20List:
            r = r -1
            continue
        random20List.append(r)

#获取剩余的样本数据
def getleftList():
    leftList= []
    global random20List
    csvSize = len(glp.getFinalCsv())
    for i in range(0,csvSize):
        if i not in random20List:
            leftList.append(i)
    return leftList



#获取剩余的设施数据
def getleftFac():
    leftFacEng,leftFacChi = gp.get_leftFacility()
    leftFacEng.insert(0,'bank')
    leftFacChi.insert(0,'银行')
    return leftFacEng,leftFacChi



#csv新增列
def reshapeCsv():
    leftFacEng,leftFacChi = getleftFac()
    csv = glp.getFinalCsv()
    copy = csv.copy()
    for each in leftFacEng:
        typeName = copy[each]
        t1 = int(typeName.quantile(1/5))
        t2 = int(typeName.quantile(2/5))
        t3 = int(typeName.quantile(3/5))
        t4 = int(typeName.quantile(4/5))
        t5 = int(typeName.quantile(5/5))
        typeList = []
        for col in typeName:
            if col in range(0,t1+1):
                typeList.append('type1')
            elif col in range(t1+1,t2+1):
                typeList.append('type2')
            elif col in range(t2+1,t3+1):
                typeList.append('type3')
            elif col in range(t3+1,t4+1): 
                typeList.append('type4')
            elif col in range(t4+1,t5+1):
                typeList.append('type5')
        copy[each+'Type'] = typeList
    return copy



#获取KNN的数据集,KNN进行线性回归
def getKNNData(facType):
    ori = reshapeCsv();
    leftList = getleftList()
    leftSampleList,leftLabelList = getCsvIndex(facType)
    copySam = ori.loc[leftList,leftSampleList].copy()
    copyRe = ori.loc[leftList,leftLabelList].copy()
    return copySam,copyRe

#使用K邻近算法
#输入 facType（标记当前label是什么）,sample(预测的样本数据),dataset(数据集dataframe),label(标签dataframe),前多少个数据
def getKNN(facType,sample,dataSet,labels,k):
    dataSetSize = dataSet.shape[0]
    diffMat = np.tile(sample,(dataSetSize,1)) - dataSet
    #进行权值的分配
    #diffMat = changeValue(facType,diffMat)
    sqDiffMat = diffMat**2
    sqDis = sqDiffMat.sum(axis=1)
    distance = sqDis**0.5
    #sortedDis = distance.argsort() #列数和 index不对应，此函数出现问题
    sortedDis = distance.sort_values()
    labelsResult = []
    sampleResult = []
    labelFirstKey = labels.keys()[0]
    for (index,r) in zip(sortedDis.index,range(k)):
        labelsResult.append(labels.loc[index,labelFirstKey])
        sampleResult.append(dataSet.loc[index].tolist())
    return sampleResult,labelsResult


#进行维度权值的分配
#facType用于来获取对应不同的分布模型的权重比
def changeValue(facType,diffMat):
    t,leftLabelList = getCsvIndex(facType)
    diffMat[t[0]] = diffMat[t[0]]*i
    diffMat[t[1]] = diffMat[t[1]]*j
    diffMat[t[2]] = diffMat[t[2]]*k
    diffMat[t[3]] = diffMat[t[3]]*l
    return diffMat


#获取KNN最终预测
def getKNNPre(sample,dataSet,labels,facType):
    sampleResult,labelsResult = getKNN(facType,sample,dataSet,labels,KNNnum)
    return max(labelsResult,key = labelsResult.count)

#使用原有数据中抽取20条进行预测,输出正确率百分比
def getPreRightPercent(facType):
    global random20List
    getrandom20List()
    dataSet,labels = getKNNData(facType)
    ori = reshapeCsv()
    count = 0
    leftSampleList,leftLabelList = getCsvIndex(facType)
    leftSample = ori.loc[random20List,leftSampleList]
    leftLabels = ori.loc[random20List,leftLabelList]
    for index in leftSample.index:
        sample = leftSample.loc[index].tolist()
        preLabel = getKNNPre(sample,dataSet,labels,facType)
        if preLabel == leftLabels.loc[index,leftLabels.keys()[0]]:
            count = count+1
    #print(facType+' percent: {:.2%}'.format(count/predicNum))
    return count/predicNum


#获取对应需要的index进行部分csv选取
#leftSampleList就是对应的bank,house对应的下标序列
#leftLabelList就是对应的标签名字,bankType
def getCsvIndex(facType):
    csv = glp.getFinalCsv()
    oriIndex = csv.keys()
    newIndex = []
    leftLabelList = []
    for each in oriIndex:
        newIndex.append(each+'Type')

    oriIndexList = oriIndex.tolist()
    oriIndexList.remove(facType)
    leftSampleList = oriIndexList
    leftLabelList.append(facType+'Type') #获取的是分类type
    #leftLabelList.append(facType) #获取的是原来的数据
    
    return leftSampleList,leftLabelList

#获取最好的拟合参数
def getPerfectFactors():
    global i,j,k,l
    factorValueList = [0.9,0.6,0.3]
    leftFacEng,leftFacChi = getleftFac()
    for facType in leftFacEng:
        for i in factorValueList:
            for j in factorValueList:
                for k in factorValueList:
                    for l in factorValueList:
                        print((i,j,k,l))
                        percentList = []
                        for count in range(20):
                            percent  =  getPreRightPercent(facType)
                            percentList.append(percent)
                        saveInPerfectFactors(percentList,facType)
        print(facType+'已完成')
                        

#把测试权重结果保存
def saveInPerfectFactors(percentList,facType):
    global i,j,k,l
    t,leftLabelList = getCsvIndex(facType)
    avgPercent = 'percent: {:.2%}'.format(sum(percentList)/len(percentList))+'\t'
    content = t[0]+'*'+str(i)+' '+t[1]+'*'+str(j)+' '+t[2]+'*'+str(k)+' '+t[3]+'*'+str(l)
    saveInFile(avgPercent+content+'\n','perfectFactors'+os.path.sep+'perfectFactors.txt')

#保存到文件
def saveInFile(content,path):
    try:
        with open(path, 'a') as f:
            f.write(content)
    except PermissionError as e:
        saveInFile(content)

if __name__ == '__main__':
    #20180320 剩余school

    #c = reshapeCsv()
    #percentList = []
    #for i in range(20):
    #    percent  =  getPreRightPercent('house')
    #    percentList.append(percent)
    #print('final avg percent: {:.2%}'.format(sum(percentList)/len(percentList)))
    #getBayesPredict(['type1','type2','type3','type4'],'bankType')
    #c = getBayesData()
    #getBayesPercent()
    #getPerfectFactors()
    pass
