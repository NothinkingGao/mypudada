#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import ssl
import os
import re
import sys
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
# 设置超时
import time
import glob
ssl._create_default_https_context = ssl._create_unverified_context
timeout = 5
socket.setdefaulttimeout(timeout)
from logger_config import logger

def get_platform():
    import platform
    sys_platform = platform.platform().lower()
    if "windows" in sys_platform:
        return "Windows"
        logger.info("Windows")
    elif "macos" in sys_platform:
        return "MacOS"
        logger.info("MacOS")
    elif "linux" in sys_platform:
        return "Linux"
        logger.info("Linux")
    else:
        logger.info("其他系统")
    return 


plat = get_platform()
if plat == "Windows":
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
elif plat == "MacOS":
    HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62', 'Cookie': ''}

HEADER_TUPLE = (list(HEADERS.keys())[0], list(HEADERS.values())[0])


class Crawler:
    # 睡眠时长
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = HEADERS # {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 30

    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, t=0.5):
        self.time_sleep = t

    # 获取后缀名
    @staticmethod
    def get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """
        :param string original_cookie:
        :param list cookies:
        :return string:
        """
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result

    # 保存图片
    def save_image(self, rsp_data, word, dir="none"):
        # if not os.path.exists("./" + word):
        #     os.mkdir("./" + word)
        # 判断名字是否重复，获取图片长度
        self.__counter = len(os.listdir(dir)) + 1
        for image_info in rsp_data['data']:
            try:
                if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                    continue
                obj_url = image_info['replaceUrl'][0]['ObjUrl']
                thumb_url = image_info['thumbURL']
                url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                time.sleep(self.time_sleep)
                suffix = self.get_suffix(obj_url)

                # 指定UA和referrer，减少403
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    HEADER_TUPLE,
                    # ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'),
                ]
                urllib.request.install_opener(opener)

                # 保存图片
                filepath = './%s/%s' % (dir, str(self.__counter) + str(suffix))
                urllib.request.urlretrieve(url, filepath)

                if os.path.getsize(filepath) < 5:
                    logger.info("下载到了空文件，跳过!")
                    os.unlink(filepath)
                    continue
            except urllib.error.HTTPError as urllib_err:
                logger.info(urllib_err)
                continue
            except Exception as err:
                time.sleep(1)
                logger.error(err)
                logger.error(url)
                logger.info("产生未知错误，放弃保存")
                continue
            else:
                logger.info("数量+1,已有" + str(self.__counter) + "张图片")
                self.__counter += 1
        return

    # 开始获取
    def get_images(self, word, dir='none'):
        search = urllib.parse.quote(word)
        # pn int 图片数
        pn = self.__start_amount

        # 如果重试retry_times,那就返回失败
        retry_times = 6

        # 目前是爬到一张图片循环就结束了
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (search, search, str(pn), self.__per_page)
            # 设置header防403
            try:
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'], page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except UnicodeDecodeError as e:
                logger.info(e)
                logger.info('-----UnicodeDecodeErrorurl:', url)
            except urllib.error.URLError as e:
                logger.info(e)
                logger.info("-----urlErrorurl:", url)
            except socket.timeout as e:
                logger.info(e)
                logger.info("-----socket timout:", url)
            else:
                # 解析json
                rsp_data = json.loads(rsp, strict=False)
                if 'data' not in rsp_data:
                    logger.info("触发了反爬机制，自动重试！")
                    time.sleep(1)
                else:
                    self.save_image(rsp_data, word, dir)
                    # 读取下一页
                    logger.info("下载下一页")
                    pn += self.__per_page
            retry_times -= 1
            if retry_times == 0:
                return False
        logger.info("下载任务结束")
        return True

    def start(self, word, total_page=1, start_page=1, per_page=30, save_name='default'):
        """
        爬虫入口
        :param word: 抓取的关键词
        :param total_page: 需要抓取数据页数 总抓取图片数量为 页数 x per_page
        :param start_page:起始页码
        :param per_page: 每页数量
        :return:
        """
        self.__per_page = per_page
        self.__start_amount = (start_page - 1) * self.__per_page

        # 目前看是爬一张图片
        self.__amount = total_page * self.__per_page + self.__start_amount
        return self.get_images(word, save_name)

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    f1 = []
    for line in lines:
        temp = json.loads(line.strip())
        f1.append(temp)
    return f1

def original_spider():
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("-w", "--word", type=str, help="抓取关键词", required=False, default='红烧鲤鱼')
        parser.add_argument("-tp", "--total_page", type=int, help="需要抓取的总页数", required=False, default=1)
        parser.add_argument("-sp", "--start_page", type=int, help="起始页数", required=False, default=1)
        parser.add_argument("-pp", "--per_page", type=int, help="每页大小", choices=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], default=1, nargs='?')
        parser.add_argument("-d", "--delay", type=float, help="抓取延时（间隔）", default=0.05)
        args = parser.parse_args()

        crawler = Crawler(args.delay)
        crawler.start(args.word, args.total_page, args.start_page, args.per_page)  # 抓取关键词为 “美女”，总数为 1 页（即总共 1*60=60 张），开始页码为 2
    else:
        
        # 如果不指定参数，那么程序会按照下面进行执行
        final_ee = 'final_ee'
        processed_json = [i.split('.')[0] for i in os.listdir(final_ee)]
        # 抓取延迟为 0.05

        json_files = glob.glob('./new_ee/*.json')

        # 加载new_ee下所有文件
        for json_file in json_files:
            # logger.info(json_file)

            # 如果是已经爬过的,就不再爬取了
            if json_file.split('/')[-1].split('.')[0] in processed_json:
                continue

            
            exit(1)
                         
        # crawler.start('美食', 1, 1, 1)  # 抓取关键词为 “美女”，总数为 1 页，开始页码为 2，每页30张（即总共 2*30=60 张）
        # crawler.start('二次元 美女', 10, 1)  # 抓取关键词为 “二次元 美女”
        # crawler.start('帅哥', 5)  # 抓取关键词为 “帅哥”

def spider_single_file(json_file,start_index = 0):
    '''
        爬取单一的json文件,如果某一条爬取失败,结束
    '''
    crawler = Crawler(0.05)

    name1,ext = os.path.splitext(json_file)
    data = read_file(f"new_ee/{json_file}")
    for idx, d in enumerate(data):
        if idx < start_index:
            continue

        # 根据文件编号创建文件夹
        save_dir = os.path.join('./images', name1, str(idx).zfill(6))
        os.makedirs(save_dir, exist_ok=True)

        # 爬取到的文件保存到这个目录下
        crawler_result = crawler.start(d['text'], 1, 1, 1, save_name=save_dir)

        # 爬取成功
        if crawler_result:
            success_write(json_file,idx)
            save_imgs = glob.glob(os.path.join(save_dir, '*'))
            data[idx]['images'] = save_imgs
            logger.info(f"save file to {save_imgs}")
        else:
            logger.info(f"use my hander to handler it ...{json_file},index:{idx}")
            continue

    # 跑完一个文件就把这个文件的json字段跟新一下
    ff = open(os.path.join('./new_ee', name1 + '.json'), 'w', encoding='utf-8')
    for d in data:
        ff.write(json.dumps(d, ensure_ascii=False) + '\n')
    ff.close()


def success_write(filename,index):
    with open("process.txt","r") as f:
        names = f.readlines()

    for i,item in enumerate(names):
        file_obj = json.loads(item)
        if file_obj["name"] == filename:
            file_obj["index"] = index
            names[i] = json.dumps(file_obj)+"\n"
            break
    
    with open("process.txt","w") as f:
        f.writelines(names)


def create_process_file():
    path = 'new_ee'  # 替换为您想要获取文件的文件夹路径

    with open("process.txt", "w") as f:
        items = list()
        for root, dirs, files in os.walk(path):
            for file in files:
                items.append(json.dumps({"name": file, "index": 0}) + "\n")

        f.writelines(items)

def main():
    #success_write("dev_4.json",5)
    #create_process_file()

    with open("process.txt","r") as f:
        lines = f.readlines()

    for item in lines:
        file_obj = json.loads(item)
        try:
            if file_obj["index"] < 99:
                spider_single_file(file_obj["name"],file_obj["index"])
            else:
                logger.info(f"{item} has run completely!")
        except Exception as e:
            logger.info(f"{item} has run error!,{str(e)}")
            continue


    logger.info("run complete.")


if __name__ == '__main__':
    main()
    
