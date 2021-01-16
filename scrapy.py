import bs4
import re
import time
import pymysql as py
import urllib.request
from urllib import parse
import requests
import random
HEADERS = ["Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0"]
user_agent = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1'
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0']
SCORE={"还行":3, "推荐":4, "力荐":5, "较差":2, "很差":1, "0":0}
headers = {"User-agent": random.choice(HEADERS)}

def get_ip_list(headers):
    url = 'http://www.xicidaili.com/nn/'
    web_data = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(web_data.text, 'lxml')
    ips = soup.find_all('tr')
    ip_list = []
    for i in range(1, len(ips)):
        ip_info = ips[i]
        tds = ip_info.find_all('td')
        ip_list.append(tds[1].text + ':' + tds[2].text)
    return ip_list


def get_random_ip(ip_list):
    proxy_list = []
    for ip in ip_list:
        proxy_list.append('http://' + ip)
    proxy_ip = random.choice(proxy_list)
    proxies = {'http': proxy_ip}
    return proxies

def load_data():
    # name = input("Please input the thing you want to search: ")
    name = "24733428"
    url = "https://movie.douban.com/subject/34962956/?from=playing_poster"
    name = parse.quote(name)
    print(name)
    # response = requests.get(url + name, headers=headers, proxies=)
    response = urllib.request.Request(url + name, headers=headers)
    response = urllib.request.urlopen(response)
    print(response)
    data = response.read().decode('utf-8')
    print(data)
    with open("baidu.html", "w+", encoding='utf-8') as f:
        f.write(data)


def allMoviesOnDisplay(cursor, proxies):
    url = "https://movie.douban.com/cinema/nowplaying/beijing/"
    response = requests.get(url, headers=headers, proxies=proxies)
    # response = urllib.request.Request(url, headers=headers)
    # response = urllib.request.urlopen(response)
    print(response)
    # response = response.read().decode('utf-8')
    '''
    with open("豆瓣电影总网页.html", "w+", encoding='utf-8') as f:
        f.write(response)
    '''
    soup = bs4.BeautifulSoup(response, 'lxml')
    nowplaying = soup.find_all('div', attrs={'id': 'nowplaying'})[0]
    tips = nowplaying.find_all("a", attrs={"class": "ticket-btn", "data-psource": "poster"})
    number = {}
    for tip in tips:
        key = tip.get('href')
        value = tip.find_all("img")[0].get('alt')
        number[key] = value
    print(len(number), "共有这么多部电影等待爬取")
    singleMovie(number, cursor, proxies)
    return number  # 返回字典：{电影url：电影名}

def singleMovie(number:dict, cursor, proxies):
    response = None
    for key in number.keys():
        response = urllib.request.Request(key, headers=headers)
        response = urllib.request.urlopen(response)
        print("当前爬取的电影为：", number[key], " url 是", key)
        response = response.read().decode('utf-8')
        '''
        with open(number[key]+".html", "w+", encoding='utf-8') as f:
            f.write(response)
        f.close()
        '''
        time.sleep(1)
        extractInfo(response, cursor, key, proxies)

def extractInfo(response, cursor, url, proxies):  # 抽取单个电影的基本信息
    # response = open("心灵奇旅.html")
    soup = bs4.BeautifulSoup(response, 'lxml')
    score_count = soup.find_all('span', attrs={'property': 'v:votes'})
    if(len(score_count) == 0):
        return
    else:
        score_count = score_count[0].next_element  # 打分的总人数,刚上映一两天的电影有时候会没有评分信息
    score = soup.find_all('strong', attrs={'property': 'v:average', 'class': 'll rating_num'})[0].string  # 总平均分
    pattern = re.compile("全部 *\d+ *条")
    element = soup.find_all('a', text=pattern)
    data = []
    for i in element:
        temp = re.findall(r"\d+", i.string)[0]
        href = i.get('href')
        data.append([temp, href])
    number = re.findall(r"\d+", url)
    data[1][1] = "https://movie.douban.com/subject/" + number[0] + "/" + data[1][1]
    data[2][1] = "https://movie.douban.com" + data[2][1]
    print("下一个要爬的电影是", number[0])  # 单个电影的长评和短评以及他们的href都在data里
    shortCommentGet(data[0][1], cursor, number[0], proxies)  # 抽取短评并写入数据库

def shortCommentGet(href,connect, MOVIEID, proxies): # 抽取单个电影的短评
    # jump to the short comment pages
    # href = "https://movie.douban.com/subject/24733428/comments?status=P"
    print("这个电影的MOVIEID为", MOVIEID)
    response = urllib.request.Request(href, headers=headers)
    response = urllib.request.urlopen(response)
    response = response.read().decode('utf-8')
    baseurl = "https://movie.douban.com/subject/"+ MOVIEID +"/comments"
    for i in range(5):
        print("-------------------当前正在访问第", i, "页短评-------------------")
        soup = bs4.BeautifulSoup(response, 'lxml')
        comments = soup.find_all('div', attrs={'class': 'comment-item'})
        for j in comments:
            comments_contain = j.find_all('span', attrs={'class': 'short'})
            user = j.find_all('a')[0].get('title')
            user_url = j.find_all('a')[0].get('href')
            user_ID = user_url.split('/')[-2]
            stamp = j.find_all('span', class_=re.compile(r"allstar.* rating"))
            if(len(stamp) > 0):
                stamp = stamp[0].get('title')# 获取每个用户的评分,豆瓣存在一部分用户的短评是没有打分的
            else:
                stamp = "0"
            user_score = SCORE[stamp]
            comments_contain = comments_contain[0].string
            info = str(MOVIEID) + "','" + user +"'," + str(user_score) + ",'" + comments_contain + "','" + user_url + "','" + user_ID +"')"
            print(info)
            try:
                flag = connect.cursor().execute("replace into short_comments (ID,user_name,user_score,user_comment, user_url, user_ID) values ('" + info)
            except py.err.ProgrammingError:
                print("录入一个信息失败----------------！！！！！！！！！！！！！！！！！！！！！！！！")
            else:
                connect.commit()
        nextpage = soup.find_all('a', attrs={'class': 'next', 'data-page': 'next'})
        if(len(nextpage) == 0):
            return  # 没有足够多的评论
        nextpage = nextpage[0].get('href')
        print("#################", nextpage, "####################\n\n")
        nextpage = baseurl + nextpage
        print(nextpage)
        try:
            response = urllib.request.Request(nextpage, headers=headers)
        except Exception:
            print("Internet connect failed .....................\n\n\n\n\n")
            return
        response = urllib.request.urlopen(response)
        response = response.read().decode('utf-8')
        time.sleep(random.randint(1, 5))

def databaseConnect(proxies):
    '''
    数据库分为basic_info, short_comments, long_comments 个表
    用户信息：user='debian-sys-maint', password='aVANykWZnldyXF2Q',
    1. basic_info的表项包括：ID,name,stars,score,comment_number,long_comment_number,income，分别对应varchar,vachar,int,float,int,int,int
    2. short_comments的表项包括：ID(varchar15)，user_name(varchar30),user_score(float),user_comment(text), user_ID(varchar(30),user_url(varchar(100)
    3. long_comments的表项包括：同上
    '''
    py.install_as_MySQLdb()
    connect = py.connect(host='127.0.0.1', user='debian-sys-maint', password='aVANykWZnldyXF2Q', port=3306, database='douban', charset='utf8mb4')
    print(connect)
    cleanDatabase(connect, "short_comments")
    cleanDatabase(connect, "basic_info")
    cursor = connect.cursor()
    '''
    number = "'123456',"
    name = "'test_movie',"
    temp = number + name + str(5) + "," + str(5.5) + "," + str(10) + "," + str(3) + "," + str(5000)
    inputs = "insert into basic_info (ID,name,stars,score,comment_number,long_comment_number,income) values (" + temp + ")"
    print(inputs)
    cursor.execute(inputs)
    connect.commit()

    cursor.execute("select * from basic_info where name = 'test_movie'")
    '''
    allMoviesOnDisplay(connect, proxies)
    connect.commit()
    connect.close()

def cleanDatabase(connect, table):
    cursor = connect.cursor()
    cursor.execute("truncate table " + table)  # 清空表
    connect.commit()

# proxies = get_ip_list(headers)
# print(proxies)
databaseConnect({"http": "http://27.191.234.69:9999"})
#load_data()