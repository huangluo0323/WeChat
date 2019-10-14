from selenium import webdriver
import requests
import re
import csv
import tkinter as tk
import tkinter.font as tkFont
import time
import json
import random

window = tk.Tk()
window.title("爬取微信公众号")
window.geometry("400x250") #窗口大小
window.resizable(0,0)  #固定窗口大小
ft1 = tkFont.Font(size=20, slant=tkFont.ITALIC) #字体样式
ft2 = tkFont.Font(size=15, slant=tkFont.ITALIC) #字体样式

#账号输入框
tk.Label(window,text="公众号账号:",font=ft2).place(x=35,y=40)
var_name = tk.StringVar()
entry_name = tk.Entry(window,width=33,textvariable=var_name,borderwidth=2) #输入框
entry_name.place(x=150,y=40)

#密码输入框
tk.Label(window,text="公众号密码：:",font=ft2,).place(x=35,y=90)
var_pwd = tk.StringVar()
entry_pwd = tk.Entry(window,width=33,textvariable=var_pwd,borderwidth=2,show='*') #输入框
entry_pwd.place(x=150,y=90)

#搜索输入框
tk.Label(window,text="搜索公众号：:",font=ft2).place(x=35,y=140)
var_vx = tk.StringVar()
entry_vx = tk.Entry(window,width=33,textvariable=var_vx,borderwidth=2) #输入框
entry_vx.place(x=150,y=140)

def get_cookie():
    #获取账号密码
    input_name = var_name.get()
    input_pwd = var_pwd.get()
    #打开浏览器
    driver = webdriver.Chrome()
    url = 'https://mp.weixin.qq.com'
    driver.get(url)

    #清空账号输入框
    driver.find_element_by_name("account").clear()
    #输入账号
    driver.find_element_by_name("account").send_keys(input_name)
    time.sleep(1)
    #清空密码输入框
    driver.find_element_by_name("password").clear()
    #输入密码
    driver.find_element_by_name("password").send_keys(input_pwd)
    time.sleep(1)
    #勾选记住账号
    driver.find_element_by_class_name("frm_checkbox_label").click()
    time.sleep(1)
    #点击登录
    driver.find_element_by_class_name("btn_login").click()
    print("请拿出手机扫描二维码登录公众号")
    time.sleep(15)
    print("登录成功")
    #获取Cookies
    cookies = driver.get_cookies()
    items = {}
    for cookie in cookies:
        items[cookie['name']] = cookie['value']
    #保存cookie
    cookie_str = json.dumps(items)
    with open('cookies.txt','w+',encoding='utf-8') as f:
        f.write(cookie_str)
    print("保存成功")
    #关闭浏览器
    driver.quit()
    get_info()
def get_info():
    #获取搜索公众号
    input_vx = var_vx.get()
    url = 'https://mp.weixin.qq.com'
    headers = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    }
    #读取保存的cookie
    with open('cookies.txt','r',encoding='utf-8') as f:
        cookie = f.read()
    cookies = json.loads(cookie)

    res = requests.get(url,headers = headers,cookies=cookies)
    token = re.findall(r'token=(\d+)',str(res.url))[0]
    #搜索微信公众号的接口url
    vx_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    params = {
        'action': 'search_biz',
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'query': input_vx,
        'begin': '0',
        'count': '5'
    }

    vx_res = requests.get(vx_url,cookies=cookies,headers=headers,params=params)
    #取搜索结果中的第一个公众号
    lists = vx_res.json().get('list')[0]
    print(lists)
    #获取fakeid
    fakeid = lists.get('fakeid')

    #微信公众号文章接口地址
    text_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    text_data = {
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'action': 'list_ex',
        'begin': '0',  # 不同页，此参数变化，变化规则为每页加5
        'count': '5',
        'query': '',
        'fakeid': fakeid,
        'type': '9'
    }
    #搜索微信公众号文章列表页
    text_res = requests.get(text_url,cookies=cookies,headers=headers,params=text_data)
    #获取文章总数
    text_num = text_res.json().get('app_msg_cnt')
    #每页五条，分页爬取
    num = int(int(text_num)/5)
    #设置起始页参数，每页加5
    begin = 0
    seq = 0
    #创建csv
    fileName = input_vx + '.csv'
    text_csv = open(fileName, 'w', newline='', encoding='utf-8-sig')
    field = ["文章标题", "文章链接"]
    writer = csv.DictWriter(text_csv, field)
    writer.writeheader()
    while num + 1 >0:
        text_data = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin': f'{str(begin)}',  # 不同页，此参数变化，变化规则为每页加5
            'count': '5',
            'query': '',
            'fakeid': fakeid,
            'type': '9'
        }
        #获取每一页文章标题跟链接，并保存
        data_res = requests.get(text_url, cookies=cookies, headers=headers, params=text_data)
        datas = data_res.json().get('app_msg_list')
        if datas:
            for data in datas:
                dict1={}
                #文章链接跟标题
                dict1["文章标题"] = data.get('title')
                dict1["文章链接"] = data.get('link')
                writer.writerow(dict1)
                seq += 1
                print(f"{dict1}\n保存成功")
                num -= 1
                begin = int(begin)
                begin += 5
                time.sleep(1)

# 按钮
btn = tk.Button(window,text="开始爬取",font=ft1,command=get_cookie)
btn.place(x=130,y=190)
window.mainloop()
