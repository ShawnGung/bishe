import requests
import urllib.parse

global i
i=0


def re():
    global i
    url = 'http://restapi.amap.com/v3/place/around?key=e053d41d5e06ae71ab79dca226e5f6e2&location=23.038,113.117&types=160100&radius=2000&offset=20&page=1&extensions=base'
    r = requests.get(url)
    i = i+1
    print(i)

def main():
    try:
        while True:
            re()
    except:
        main()


if __name__ == '__main__':
    main()
