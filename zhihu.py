#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Required
- requests (必须)
- pillow (可选)
Info
- author : "xchaoinfo"
- email  : "xchaoinfo@qq.com"
- date   : "2016.2.4"
Update
- name   : "wangmengcn"
- email  : "eclipse_sv@163.com"
- date   : "2016.4.21"
'''
import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
try:
    from PIL import Image
except:
    pass
from lxml import etree


# 构造 Request headers
agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'
headers = {
    "Host": "www.zhihu.com",
    "Referer": "https://www.zhihu.com/",
    'User-Agent': agent
}

# 使用登录cookie信息
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")


class checkyanzhi():
    def __init__(self, imagebase64):
        self.ss = requests.session()
        #上传图片地址
        self.uploadurl = 'https://kan.msxiaobing.com/Api/Image/UploadBase64'
        #首页地址(获取tid的地址)
        self.yanzhiurl = 'https://kan.msxiaobing.com/ImageGame/Portal?task=yanzhi'
        #得到分数的地址
        self.processurl = 'https://kan.msxiaobing.com/Api/ImageAnalyze/Process'
        #图片的base64
        self.imagebase64 = imagebase64
    def upload(self):
        z = self.ss.post(self.uploadurl, self.imagebase64)
        ret = z.json()
        """
        返回值
        {u'Host':u'https://mediaplatform.msxiaobing.com',
         u'Url' : u'/image/fetchimage?key=JMGsDUAgbwOliRCoPQrsio_hk1s4N2occwMgAoCWZZ9JTwLdRLjCGRDKoQM'}
        """
        return '%s%s'%(ret['Host'],ret['Url'])

    def process(self):
        z1 = self.ss.get(self.yanzhiurl)
        #获取tid
        tid = etree.HTML(z1.content).xpath('//input[@name="tid"]/@value')[0]
        tm = time.time()
        data = {'MsgId':'%s' %int(tm*1000),'CreateTime':'%s' %int(tm),
                'Content[imageUrl]':self.upload()}
        z2 = self.ss.post(url=self.processurl,params={"service":"yanzhi",
                "tid":tid},data=data)

        ret = z2.json()['content']['text']
        mark = re.findall(r"\d+\.?\d?", ret)
        return mark[0]

def vote_up(answer_id):
    url = 'https://www.zhihu.com/node/AnswerVoteBarV2'
    data = {'method':'vote_up',
            'params':'{"answer_id":"%s"}' %answer_id}
    #获取xsrf
    _xsrf = get_topic_xsrf()
    #把_xsrf添加到浏览器头
    headers['X-Xsrftoken'] = _xsrf
    z2 = session.post(url, data=data, headers=headers)
    if z2.status_code == 200:
        #如果msg不为空,表示点赞出错
        if z2.json()['msg'] != None:
            print(z2.json()['msg'])
        else:
            print(u'%s点赞ok' %answer_id)

def get_xsrf():
    '''_xsrf 是一个动态变化的参数'''
    index_url = 'https://www.zhihu.com'
    # 获取登录时需要用到的_xsrf
    index_page = session.get(index_url, headers=headers)
    html = index_page.text
    pattern = r'name="_xsrf" value="(.*?)"'
    # 这里的_xsrf 返回的是一个list
    _xsrf = re.findall(pattern, html)
    return _xsrf[0]


# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    with open('captcha.jpge', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpge')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpge 手动输入' % os.path.abspath('captcha.jpge'))
    captcha = input("please input the captcha\n>")
    return captcha


def isLogin():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=headers, allow_redirects=False).status_code
    if login_code == 200:
        return True
    else:
        return False


def login(secret, account):
    _xsrf = get_xsrf()
    headers["X-Xsrftoken"] = _xsrf
    headers["X-Requested-With"] = "XMLHttpRequest"
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", account):
        print("手机号登录 \n")
        post_url = 'https://www.zhihu.com/login/phone_num'
        postdata = {
            '_xsrf': _xsrf,
            'password': secret,
            'phone_num': account
        }
    else:
        if "@" in account:
            print("邮箱登录 \n")
        else:
            print("你的账号输入有问题，请重新登录")
            return 0
        post_url = 'https://www.zhihu.com/login/email'
        postdata = {
            '_xsrf': _xsrf,
            'password': secret,
            'email': account
        }
    # 不需要验证码直接登录成功
    login_page = session.post(post_url, data=postdata, headers=headers)
    login_code = login_page.json()
    if login_code['r'] == 1:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        postdata["captcha"] = get_captcha()
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = login_page.json()
        print(login_code['msg'])
    # 保存 cookies 到文件，
    # 下次可以使用 cookie 直接登录，不需要输入账号和密码
    session.cookies.save()

try:
    input = raw_input
except:
    pass


def get_topic_xsrf():
    z = session.get('https://www.zhihu.com/topic#胸部', headers=headers)
    _xsrf = etree.HTML(z.content).xpath('//input[@name="_xsrf"]/@value')[0]
    return _xsrf

def download_image(urllist):
    old_host = headers["Host"]
    headers["Host"] = "pic2.zhimg.com"
    ir = session.get('https://pic2.zhimg.com/v2-989525480828935eadb6a9a91af62b89_b.jpg', headers=headers)
    #print(ir.status_code)
    for url in urllist:
        print(url)
        ir = session.get(url, headers=headers)
        if ir.status_code == 200:
            open('images/%s'%(url.split(r'/')[-1]), "wb").write(ir.content)
    headers["Host"] = old_host


def getimgsrc():
    #获取xsrf
    _xsrf = get_topic_xsrf()
    # 把_xsrf 添加到浏览器头
    headers['X-Xsrftoken'] = _xsrf
    data = {
        'method' : 'next',
        'params' : '{"offset":0,"topic_id":11385,"feed_type":"smart_feed"}',
    }
    z1 = session.post('https://www.zhihu.com/node/TopicFeedList', data=data,headers=headers)
    #把所有的html代码拼接起来
    html = ''.join(z1.json()['msg'])
    ll = etree.HTML(html)
    #获取当前回答的所有内容
    contents = ll.xpath('//textarea[@class="content"]/text()')
    #print("len(contents):", (len(contents)))
    for i in range(len(contents)):
        #提取出其中的图片地址
        images = etree.HTML(contents[i]).xpath('//img/@src')
        #print(len(images))
        download_image(images)
        if len(images) != 0:
            answer_id = ll.xpath('//meta[@itemprop="answer-id"]/@content')[i]
            #print(answer_id)
            title = ll.xpath('//div[@class="feed-content"]/h2/a/text()')[i].strip()
            href = ll.xpath('//div[@class="zm-item-rich-text expandable js-collapse-body"]/@data-entry-url')[i]
            #时间戳
            data_score = ll.xpath('//div[@class="feed-item feed-item-hook  folding"]/@data-score')[i]
            #print(answer_id, title, href, data_score)
    """
    """

def scrapy_topic():
    url = 'https://www.zhihu.com/followed_topics?offset=0&limit=80'
    z = session.get(url, headers=headers)

    topic = z.json()['payload']

    print(len(topic))
    getimgsrc()


if __name__ == '__main__':
    if isLogin():
        print('您已经登录')
    else:
        account = input('请输入你的用户名\n>  ')
        secret = input("请输入你的密码\n>  ")
        login(secret, account)

    scrapy_topic()
