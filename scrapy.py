import bs4
import re
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
    singleMovie(number)
    return number

def singleMovie(number:dict):
    response = None
    for key in number.keys():
        response = urllib.request.Request(key, headers=headers)
        response = urllib.request.urlopen(response)
        print("当前爬取的电影为：", number[key], " url 是", key)
        response = response.read().decode('utf-8')
        with open(number[key]+".html", "w+", encoding='utf-8') as f:
            f.write(response)
        f.close()
        time.sleep(1)
    extractInfo()

def extractInfo():  # 抽取单个电影的基本信息
    response = open("心灵奇旅.html")
    soup = bs4.BeautifulSoup(response, 'lxml')
    score_count = soup.find_all('span', attrs={'property': 'v:votes'})[0].next_element  # 打分的总人数
    score = soup.find_all('strong', attrs={'property': 'v:average', 'class': 'll rating_num'})[0].string  # 总平均分
    print(score_count, "\n", score)
    pattern = re.compile("全部 *\d+ *条")
    element = soup.find_all('a', text=pattern)
    data = []
    for i in element:
        temp = re.findall(r"\d+", i.string)[0]
        href = i.get('href')
        data.append([temp, href])
    number = re.findall(r"\d+", data[2][1])
    data[1][1] = "https://movie.douban.com/subject/" + number[0] + "/" + data[1][1]
    data[2][1] = "https://movie.douban.com" + data[2][1]
    print(data)  # 单个电影的长评和短评以及他们的href都在data里


def databaseConnect():
    '''
    数据库分为basic_info, short_comments, long_comments 个表
    1. basic_info的表项包括：ID,name,stars,score,comment_number,long_comment_number,income，分别对应varchar,vachar,int,float,int,int,int
    2. short_comments的表项包括：ID(varchar15)，user_name(varchar30),user_score(float),user_comment(text)
    3. long_comments的表项包括：同上
    '''
    py.install_as_MySQLdb()
    connect = py.connect(host='127.0.0.1', user='debian-sys-maint', password='aVANykWZnldyXF2Q', port=3306, database='douban', charset='utf8')
    print(connect)
    cleanDatabase(connect)
    cursor = connect.cursor()
    number = "'123456',"
    name = "'test_movie',"
    temp = number + name + str(5) + "," + str(5.5) + "," + str(10) + "," + str(3) + "," + str(5000)
    inputs = "insert into basic_info (ID,name,stars,score,comment_number,long_comment_number,income) values (" + temp + ")"
    print(inputs)
    cursor.execute(inputs)
    connect.commit()

    cursor.execute("select * from basic_info where name = 'test_movie'")
    connect.close()

def cleanDatabase(connect):
    cursor = connect.cursor()
    cursor.execute("truncate table basic_info")  # 清空表
    connect.commit()

# load_data()
#allMoviesOnDisplay()
#databaseConnect()
extractInfo()