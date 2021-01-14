import numpy
import matplotlib
import bs4
import requests
import time
import pymysql as py
import urllib.request
from urllib import parse

headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
user_agent = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1'
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0']


def load_data():
    # name = input("Please input the thing you want to search: ")
    name = "24733428"
    url = "https://movie.douban.com/subject/" + name + "/?from=showing"
    name = parse.quote(name)
    print(name)
    response = urllib.request.Request(url + name, headers=headers)
    response = urllib.request.urlopen(response)
    print(response)
    data = response.read().decode('utf-8')
    print(data)
    with open("baidu.html", "w+", encoding='utf-8') as f:
        f.write(data)


def allMoviesOnDisplay():
    url = "https://movie.douban.com/cinema/nowplaying/beijing/"
    response = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(response)
    print(response)
    response = response.read().decode('utf-8')
    with open("豆瓣电影总网页.html", "w+", encoding='utf-8') as f:
        f.write(response)
    soup = bs4.BeautifulSoup(response, 'lxml')
    tips = soup.find_all("a", attrs={"class": "ticket-btn", "data-psource": "poster"})
    number = {}
    for tip in tips:
        key = tip.get('href')
        value = tip.find_all("img")[0].get('alt')
        number[key] = value
    print(number)
    return number

def DatabaseConnect():
    # py.install_as_MySQLdb()
    connect = py.connect(host='127.0.0.1', user='root', password='990304', database='douban', port=3306, charset='utf8')
    print(connect)

# load_data()
#allMoviesOnDisplay()
DatabaseConnect()
