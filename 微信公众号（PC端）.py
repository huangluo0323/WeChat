import csv
import requests
import json
import time
from datetime import datetime
import re
#关闭证书验证警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Wechat_Get(object):
    def __init__(self,biz,offset,appmsg_token,pass_ticket,cookie,key):
        self.csv = open('公众号信息.csv', 'w', newline='', encoding='utf-8-sig')
        self.field = ["标题","作者","发布时间","阅读量","评论数","在看","原文链接"]
        self.writer = csv.DictWriter(self.csv, self.field)
        self.writer.writeheader()

        self.biz =biz   #公众号标识
        self.offset = offset
        self.msg_token = appmsg_token  #票据（非固定）
        self.pass_ticket = pass_ticket  #票据（非固定）
        self.key = key
        self.cookie = cookie

        #请求头
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.5;q=0.4',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/4.0.1219.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MjM5MzUwMjU2MA==&scene=124&uin=MTI1NjQ2NTc4MQ%3D%3D&key=e69c6751254f35b85674b83abb8623040ca8f00033c2687d1b05fa5e9a988d56a49a8bb48f1a0edac31f97408c375b34bff3f46b7732161647fc5d94d0dd0bb6aad7e9754f051ffc11bc2f7d0b0fcea5&devicetype=Windows+7&version=62060841&lang=zh_CN&a8scene=7&pass_ticket=EBnA0vKvBzMmTeFsKWuYKmDHjVAMaKGytRTfhU0qrtWtxRVXMK9wjrvcceyT0UyE&winzoom=1',
            'Connection': 'keep-alive',
            'Host': 'mp.weixin.qq.com',
            'Cookie':self.cookie
        }

    def vx_start(self):
        '''请求获取公众号的文章接口'''
        offset = self.offset
        while True:
            api = f'http://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={self.biz}&f=json&offset={offset}&count=10&is_ok=1&scene=124&uin=MTI1NjQ2NTc4MQ%3D%3D&key={self.key}&pass_ticket={self.pass_ticket}&wxtoken=&appmsg_token={self.msg_token}&x5=0&f=json'
            res = requests.get(url=api,headers=self.headers,verify=False).json()
            #状态信息
            ret = res.get('ret')
            status = res.get('errmsg')
            if ret == 0 or status == 'ok':
                print("开始爬取")
                offset= res['next_offset']
                general_msg_list = res['general_msg_list']
                #获取文章列表
                msg_list = json.loads(general_msg_list)['list']
                # time.sleep(1)
                for msg in msg_list:
                    dict1={}
                    comm_msg_info = msg['comm_msg_info'] #文章信息
                    msg_id = comm_msg_info['id'] #文章id
                    post_time = datetime.fromtimestamp(comm_msg_info['datetime'])  # 发布时间
                    msg_type = comm_msg_info['type']  # 文章类型
                    app_msg_ext_info = msg.get('app_msg_ext_info')  # 文章原数据
                    if app_msg_ext_info:
                        #本次推送的第一篇文章
                        self._parse_articles(app_msg_ext_info, msg_id, post_time)
                        #本次推送剩余文章
                        multi_app_msg_item_list = app_msg_ext_info.get('multi_app_msg_item_list')
                        if multi_app_msg_item_list:
                            for item in multi_app_msg_item_list:
                                msg_id = item['fileid']  # 文章id
                                if msg_id == 0:
                                    msg_id = int(time.time() * 1000)  # 设置唯一id,解决部分文章id=0出现唯一索引冲突的情况
                                self._parse_articles(item, msg_id, post_time)
            else:
                print('需要更新数据')
                break

    def _parse_articles(self, info, msg_id, post_time):
        """解析嵌套文章数据并保存入库"""
        post_time = post_time #发布时间
        title = info.get('title')  # 标题
        cover = info.get('cover')  # 封面图
        author = info.get('author')  # 作者
        digest = info.get('digest')  # 关键字
        source_url = info.get('source_url')  # 原文地址
        content_url = info.get('content_url')  # 微信地址
        ext_data = json.dumps(info, ensure_ascii=False)  # 原始数据
        content_url = content_url.replace('amp;', '').replace('#wechat_redirect', '').replace('http', 'https')

        # time.sleep(3)
        self._parse_article_detail(content_url,post_time,title,author)

    def _parse_article_detail(self,content_url,post_time,title,author):
        """从文章页提取相关参数用于获取评论"""
        content_url=content_url
        post_time=post_time
        title=title
        author=author
        try:
            html = requests.get(content_url, headers=self.headers, verify=False).text
        except:
            print('获取评论失败' + content_url)
        else:
            str_comment = re.search(r'var comment_id = "(.*)" \|\| "(.*)" \* 1;', html)
            str_msg = re.search(r"var appmsgid = '' \|\| '(.*)'\|\|", html)
            str_token = re.search(r'window.appmsg_token = "(.*)";', html)
            if str_comment and str_msg and str_token:
                comment_id = str_comment.group(1)  # 评论id(固定)
                app_msg_id = str_msg.group(1)  # 票据id(非固定)
                appmsg_token = str_token.group(1)  # 票据token(非固定)
                # 缺一不可
                if  app_msg_id and comment_id:
                    self._crawl_comments(app_msg_id, comment_id,content_url,post_time,title,author)

    def _crawl_comments(self, app_msg_id, comment_id,content_url,post_time,title,author):
        """抓取文章的评论"""
        #阅读量链接
        api1 = f'https://mp.weixin.qq.com/mp/getappmsgext?f=json&mock=&uin=MTI1NjQ2NTc4MQ%253D%253D&key={self.key}&pass_ticket={self.pass_ticket}&wxtoken=777&devicetype=Windows%26nbsp%3B7&clientversion=62060841&__biz={self.biz}&appmsg_token={self.msg_token}&x5=0&f=json'
        #评论链接
        api=f'https://mp.weixin.qq.com/mp/appmsg_comment?action=getcomment&scene=0&__biz={self.biz}&appmsgid={app_msg_id}&idx=1&comment_id={comment_id}&offset=0&limit=100&uin=777&key=777&pass_ticket={self.pass_ticket}&wxtoken=777&devicetype=android-26&clientversion=26060739&appmsg_token={self.msg_token}&x5=1&f=json'
        resp = requests.get(api, headers=self.headers,verify=False).json()
        # time.sleep(3)
        resp1 = requests.get(api1, headers=self.headers,verify=False).json()
        # time.sleep(3)
        ret1 = resp1['appmsgstat']['ret']
        if ret1 == 0 :
            appmsgstat = resp1['appmsgstat']
            for msgstat in appmsgstat:
                dict1={}
                read_num = msgstat.get('read_num') #阅读量
                like_num  = msgstat.get('like_num') #在看
        ret, status = resp['base_resp']['ret'], resp['base_resp']['errmsg']
        if ret == 0 or status == 'ok':
            elected_comment = resp['elected_comment']
            content_num = len(elected_comment) #评论数
            dict1 = {}
            dict1["评论数"] = content_num
            dict1['标题'] = title
            dict1['作者'] = author
            dict1['原文链接'] = content_url
            dict1['发布时间'] = post_time
            # dict1["阅读量"] = read_num
            # dict1["在看"] = like_num
            print(title)
            self.save_info(dict1)
            for comment in elected_comment:
                nick_name = comment.get('nick_name')  # 昵称
                logo_url = comment.get('logo_url')  # 头像
                comment_time = datetime.fromtimestamp(comment.get('create_time'))  # 评论时间
                content = comment.get('content')  # 评论内容
                content_id = comment.get('content_id')  # id
                like_num = comment.get('like_num')  # 点赞数
                reply_list = comment.get('reply')['reply_list']  # 回复数据


    def save_info(self,item):
        self.writer.writerow(item)
        print("保存数据成功！")


if __name__ == '__main__':
    key = '2bc8ce6de4a79add458946bfcd381908c4540c5b6b2f772336a691f07c9d00df280b653c61ac36147a4da46c011a17fcfcbdc0a36c55b9879a4b44eef372add985cfbad7f6f44ab81e5586de03356ddf'
    biz = 'MzI4NDIwMzAzNQ=='
    offset = '10'
    appmsg_token ='1030_CCdBqivxgOwGZZgvuXy5XOhFJWkj9-bnMuCc9w~~'
    pass_ticket = 'KKGCBk1et8glzY9y+OqUqeEm62w76dMqJooRw0ww3t41rvDGFv2nLYscsvVT+bDU'
    cookie='rewardsn=; wxtokenkey=777; wxuin=1256465781; devicetype=android-28; version=27000739; lang=zh_CN; pass_ticket=KKGCBk1et8glzY9yOqUqeEm62w76dMqJooRw0ww3t41rvDGFv2nLYscsvVTbDU; wap_sid2=CPXKkNcEElxyS25LUFMybEU0cWZfWm9nZ25MQ3FvakNHRENfQUxJdEF1aHh0T0VxMzdrMUUxLV9wdWtQdXlfeTl0UVVEM0lRckp5bU1DT1A1ck1ORUs0WERfM3BCUVlFQUFBfjC3nYbtBTgNQJVO'

    run = Wechat_Get(biz,offset,appmsg_token,pass_ticket,cookie,key)
    run.vx_start()
