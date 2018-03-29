import pandas as pd
dlist = {'长沙市':[[1,2],[3,4],[5,6]],'广州市':[[22,3],[1,2]]}



for each in dlist:
    for pos in dlist[each]:
        dataframe = pd.DataFrame({'lat':[1,3,5,7],'lng':[2,4,6,7]})
        dataframe.to_csv('test'+ each +'.csv')
    


