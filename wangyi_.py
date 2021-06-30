import pandas as pd
import requests
import json
from typing import Dict
import os
from pathlib import Path
import datetime
import time
from tqdm import tqdm
import traceback
from bs4 import BeautifulSoup
import re

# 匹配html文档中的所有标签，用于保留文本,同时保留img标签（保存图片）                                    #不除去img标签      ----去除i标签----
PATT_DEL_HTML_TAG = re.compile(r"(<style>[\s\S]+?</style>)|(<script[\s\S]*?>[\s\S]+?</script>)|(<[^i]+?.*? *.*?>)|(<i .+?>)|(</*i>)")

# 要爬取的新闻分类地址
url_list = {'国内': ['https://temp.163.com/special/00804KVA/cm_guonei.js?callback=data_callback',
                   'https://temp.163.com/special/00804KVA/cm_guonei_0{}.js?callback=data_callback'],
            '国际': ['https://temp.163.com/special/00804KVA/cm_guoji.js?callback=data_callback',
                   'https://temp.163.com/special/00804KVA/cm_guoji_0{}.js?callback=data_callback'],
            '军事': ['https://temp.163.com/special/00804KVA/cm_war.js?callback=data_callback',
                   'https://temp.163.com/special/00804KVA/cm_war_0{}.js?callback=data_callback'],
            '航空': ['https://temp.163.com/special/00804KVA/cm_hangkong.js?callback=data_callback&a=2',
                   'https://temp.163.com/special/00804KVA/cm_hangkong_0{}.js?callback=data_callback&a=2'],
            '科技': ['https://tech.163.com/special/00097UHL/tech_datalist.js?callback=data_callback',
                   'https://tech.163.com/special/00097UHL/tech_datalist_0{}.js?callback=data_callback'],
            "财经": ['https://money.163.com/special/00259BVP/news_flow_index.js?callback=data_callback',
                   'https://money.163.com/special/00259BVP/news_flow_index_0{}.js?callback=data_callback'],
            "股票": ['https://money.163.com/special/002557S6/newsdata_gp_index.js?callback=data_callback',
                   'https://money.163.com/special/002557S6/newsdata_gp_index_0{}.js?callback=data_callback'],
            "体育": ['https://sports.163.com/special/000587PR/newsdata_n_index.js?callback=data_callback',
                   'https://sports.163.com/special/000587PR/newsdata_n_index_0{}.js?callback=data_callback'],
            "NBA": ['https://sports.163.com/special/000587PK/newsdata_nba_index.js?callback=data_callback',
                    'https://sports.163.com/special/000587PK/newsdata_nba_index_0{}.js?callback=data_callback'],
            "教育": ['https://edu.163.com/special/002987KB/newsdata_edu_hot.js?callback=data_callback',
                   'https://edu.163.com/special/002987KB/newsdata_edu_hot_0{}.js?callback=data_callback'],
            "房产": ['https://house.163.com/special/000798KV/sh_float_yaowen.js?callback=data_callback',
                   'https://house.163.com/special/000798KV/sh_float_yaowen_0{}.js?callback=data_callback'],
            "旅游": ['https://travel.163.com/special/00067VEJ/newsdatas_travel.js?callback=data_callback',
                   'https://travel.163.com/special/00067VEJ/newsdatas_travel_0{}.js?callback=data_callback'],
            "女人": ['https://lady.163.com/special/00264OOD/data_nd_sense.js?callback=data_callback',
                   'https://lady.163.com/special/00264OOD/data_nd_sense_0{}.js?callback=data_callback'],
            "智能": ['https://tech.163.com/special/00097UHL/smart_datalist.js?callback=data_callback',
                   'https://tech.163.com/special/00097UHL/smart_datalist_0{}.js?callback=data_callback'],
            "手机": ['https://mobile.163.com/special/index_datalist/?callback=data_callback',
                   'https://mobile.163.com/special/index_datalist_0{}/?callback=data_callback'],
            "娱乐": ['https://ent.163.com/special/000380VU/newsdata_index.js?callback=data_callback',
                   'https://ent.163.com/special/000380VU/newsdata_index_0{}.js?callback=data_callback'],
            "艺术": ['https://art.163.com/special/00999815/art_redian_api.js?callback=data_callback',
                   'https://art.163.com/special/00999815/art_redian_api_0{}.js?callback=data_callback'],

            }



def get_url_data(url: str = "https://temp.163.com/special/00804KVA/cm_guonei.js?callback=data_callback"):
    respond = requests.get(url)
    content: str = respond.text
    return content


def deal_category_url_data(url: str):
    doc_urls = {}
    try:
        content = get_url_data(url)
    except Exception as e:
        print("------error:", content)
        traceback.print_exc()
        return doc_urls
    if "data_callback" not in content:
        return doc_urls
    # 去除content中的data_callback(..)
    content = content.replace("data_callback", "")
    content = content[1:-1]
    try:
        content_json_list: list = json.loads(content)
    except Exception as e:
        if content.startswith("(") or content.endswith(")"):
            content = content.strip("(")
            content = content.strip(")")
            content_json_list: list = json.loads(content)
        else:
            print("error-----------:",content)
            traceback.print_exc()
            return doc_urls
    for content_json in  content_json_list:
        # {'title': '陈经：让网友“沸腾”的中国芯片产能到底如何？', 'digest': '',
        #  'docurl': 'https://www.163.com/news/article/GDJ7SNIJ0001899O.html',
        #  'commenturl': 'https://comment.tie.163.com/GDJ7SNIJ0001899O.html', 'tienum': 17661, 'tlastid': '',
        #  'tlink': 'https://www.163.com/news/article/GDJ7SNIJ0001899O.html', 'label': '其它',
        #  'keywords': [{'akey_link': 'https://news.163.com/keywords/8/a/82af7247/1.html', 'keyname': '芯片'},
        #               {'akey_link': 'https://news.163.com/keywords/4/2/4e2d56fd/1.html', 'keyname': '中国'},
        #               {'akey_link': 'https://news.163.com/keywords/5/4/5149523b/1.html', 'keyname': '光刻'}],
        #  'time': '06/28/2021 14:04:33', 'newstype': 'article', 'pics3': [], 'channelname': 'guonei', 'source': '观察者网',
        #  'point': '60',
        #  'imgurl': 'http://cms-bucket.ws.126.net/2021/0628/14cc9c63p00qvee6w000yc000cj00ekc.png',
        #  'add1': '', 'add2': '', 'add3': ''}
        doc_urls[content_json["title"]] = content_json
    return doc_urls

def spider_category_data():
    for name, catrgory_urls in tqdm(url_list.items()):
        doc_urls:Dict = deal_category_url_data(catrgory_urls[0])
        for i in range(2,10):
            time.sleep(1)
            url = catrgory_urls[1].format(i)
            doc_urls_temp = deal_category_url_data(url)
            if len(doc_urls_temp):
                break
            doc_urls.update(doc_urls_temp)
        with open(os.path.abspath(os.path.join(Path(__file__).parent, "wangyi_data", "category_url_data", f"{name}-{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.json")), "w", encoding='utf-8') as f:
            json.dump(doc_urls, f, ensure_ascii = False)

def deal_article_url_data(url: str = "https://www.163.com/money/article/GDLU786L00258105.html"):
    content: str = get_url_data(url)
    soup = BeautifulSoup(content, 'lxml')
    # 获取文章主体节点 <div class = "post_body">....</div>
    ariticle_content_html = soup.select(".post_body")[0]
    ariticle_content_contain_imgTag = PATT_DEL_HTML_TAG.sub("", str(ariticle_content_html))


    ariticle_content = re.sub(r"[ ]+", " ", ariticle_content)   #将大段的空格字符 替换成当个空格
    ariticle_content = re.sub(r"[\n]+", "\n", ariticle_content)   #将大段的换行字符 替换成换行

    return ariticle_content

if __name__ == "__main__":
    # 获取url
    # spider_category_data()
    deal_article_url_data()



