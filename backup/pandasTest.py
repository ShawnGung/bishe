import pandas as pd

f=open('长沙市-住宅.csv') #解决pandas读取中文名的文件名问题
data = pd.read_csv(f,encoding='utf-8') #解决编码问题utf-8
first_rows = data.head(5)
print(first_rows)
