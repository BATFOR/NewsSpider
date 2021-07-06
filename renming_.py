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
import uuid
from pathlib import Path
import pandas as pd
import traceback
from urllib.parse import urlparse

PARENT_DIR = os.path.abspath(Path(__file__).parent)

# 匹配html文档中的所有标签，用于保留文本,同时保留img标签（保存图片）                                    #不除去img标签      ----去除i标签----
PATT_DEL_HTML_TAG = re.compile(r"(<style>[\s\S]+?</style>)|(<script[\s\S]*?>[\s\S]+?</script>)|(<[^i]+?.*? *.*?>)|(<i .+?>)|(</*i>)")

PATT_IMG_EXTRACT = re.compile(r"<img.+?src=(\".+?\").*?/>", re.M)
# 要爬取的新闻分类地址
url_list = {"房产": "http://house.people.com.cn/GB/194441/index{}.html",
            "房产-人民楼视": "http://house.people.com.cn/GB/164291/index{}.html",
            "房产-公司新闻": "http://house.people.com.cn/GB/164306/index{}.html",
            "科技": "http://scitech.people.com.cn/GB/1057/index{}.html",
            "汽车": "http://auto.people.com.cn/GB/435243/index{}.html",
            "金融": "http://money.people.com.cn/GB/218900/index{}.html",
            "公益": "http://gongyi.people.com.cn/GB/151650/index{}.html",
            "游戏": "http://game.people.com.cn/GB/48661/index{}.html",
            "娱乐": "http://ent.people.com.cn/GB/86955/index{}.html",
            "美丽乡村": "http://country.people.com.cn/GB/419851/index{}.html",
            "IT": "http://it.people.com.cn/GB/243510/index{}.html",
            "军事-滚动新闻": "http://military.people.com.cn/GB/172467/index{}.html",
            "军事-高层动态": "http://military.people.com.cn/GB/52963/index{}.html",
            "军事-国防部": "http://military.people.com.cn/GB/115150/index{}.html",
            "军事-本网原创": "http://military.people.com.cn/GB/52936/index{}.html",
            "军事-中国军情": "http://military.people.com.cn/GB/367527/index{}.html",
            "军事-国际军情": "http://military.people.com.cn/GB/1077/index{}.html",
            "军事-热点解读": "http://military.people.com.cn/GB/367540/index{}.html",
            "军事-评论": "http://military.people.com.cn/GB/42969/index{}.html",
            "教育-滚动新闻": "http://edu.people.com.cn/GB/1053/index{}.html",
            "教育-原创": "http://edu.people.com.cn/GB/367001/index{}.html",
            "教育-留学": "http://edu.people.com.cn/GB/204387/204389/index{}.html",
            "教育-幼教": "http://edu.people.com.cn/GB/226718/index{}.html",
            "教育-中小学": "http://edu.people.com.cn/GB/227057/index{}.html",
            "教育-大学": "http://edu.people.com.cn/GB/227065/index{}.html",
            "教育-职业教育": "http://edu.people.com.cn/GB/427940/index{}.html",
            "经济-科技": "http://finance.people.com.cn/GB/70846/index{}.html",
            }
request_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36",
    "Cookie": "sso_c=0; sfr=1; _ma_tk=5ma4xirnrd39xl1g2gv9sjw1ns2eanxw; wdcid=6c73af29648f8795; _ma_starttm=1624864743647; _ma_is_new_u=0; SL_wptGlobTipTmp=1; SL_GWPT_Show_Hide_tmp=1; wdses=23d7048af8937f6b; ALLYESID4=15A10029C6B9609F; wdlast=1625148415"
    }  # 设置请求头，字典格式

if os.path.exists(os.path.join(PARENT_DIR, "renmin_data", "img_url2relativePath_dict.json")):
    with open(os.path.join(PARENT_DIR, "renmin_data", "img_url2relativePath_dict.json"), 'r', encoding='utf-8') as f:
        img_url2relativePath_dict = json.load(f)
else:
    img_url2relativePath_dict = {}


def get_url_data(url: str = "http://house.people.com.cn/GB/194441/index.html"):
    respond = requests.get(url, headers=request_header)
    respond.encoding = respond.apparent_encoding
    content: str = respond.text
    return content


def deal_category_url_data(url: str = "http://house.people.com.cn/GB/194441/index.html"):
    urlparse_result = urlparse(url)
    doc_urls = {}
    try:
        content = get_url_data(url)
    except Exception as e:
        print("------error:", content)
        traceback.print_exc()
        return doc_urls
    try:
        soup = BeautifulSoup(content,'lxml')
    except Exception as e:
        traceback.print_exc()
        return doc_urls
    a_tags = soup.select("li>a")
    for a_tag in a_tags:
        href = a_tag.attrs["href"]
        title = str(a_tag.string)
        if not href.startswith("http") and href.startswith("/"):
            doc_url = urlparse_result.scheme + "://" + urlparse_result.netloc + href
            doc_urls[doc_url] = title
        elif href.startswith("http"):
            doc_urls[href] = title
        # 还存在其它不正确href形式， 不处理
    return doc_urls


def spider_category_data():
    count_to_stop_add = 0
    for name, category_url in tqdm(url_list.items()):
        if name not in ["经济-科技"]:  #特例数据重新爬取
            continue
        doc_urls = {}
        for i in range(1, 50):
            time.sleep(1)
            url = category_url.format(i)
            doc_urls_temp = deal_category_url_data(url)
            if len(doc_urls_temp) == 0:
                count_to_stop_add += 1
            if count_to_stop_add > 5: #5次返回结果，说明后续URL无效
                break
            doc_urls.update(doc_urls_temp)
        with open(os.path.abspath(os.path.join(Path(__file__).parent, "renmin_data", "category_url_data",
                                               f"{name}-{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.json")),
                  "w", encoding='utf-8') as f:
            json.dump(doc_urls, f, ensure_ascii=False)


def deal_article_url_data(url: str = "http://finance.people.com.cn/n1/2021/0610/c432208-32127309.html"):
    urlparse_result = urlparse(url)
    imgs = set()
    imgs_saved_path = []
    try:
        content: str = get_url_data(url)
    except Exception as e:
        print("---------------------------error article url:",url)
        traceback.print_exc()
        return "", []
    soup = BeautifulSoup(content, 'lxml')
    # 获取文章主体节点 <div class = "post_body">....</div>
    try:
        ariticle_content_html = soup.select(".rm_txt_con")[0]
    except Exception as e:
        traceback.print_exc()
        return "", []
    ariticle_content_contain_imgTag = PATT_DEL_HTML_TAG.sub("", str(ariticle_content_html))

    def deal_img(x):
        for group in x.groups():
            # print(group)
            url = group.strip('"')
            if not url.startswith("http") and url.startswith("/"):
                url = urlparse_result.scheme + "://" + urlparse_result.netloc + url
            elif url.startswith("http"):
                pass
            # 还存在其它不正确url形式， 不处理
            imgs.add(url)
        return ""

    ariticle_content = PATT_IMG_EXTRACT.sub(deal_img, ariticle_content_contain_imgTag)

    ariticle_content = re.sub(r"[ ]+", " ", ariticle_content)  # 将大段的空格字符 替换成当个空格
    ariticle_content = re.sub(r"[\s]{2,}", "\n", ariticle_content)  # 将大段的换行字符 替换成换行

    def download_img(img_url):
        """
        下载图片
        :param img_url: 图片的网络地址
        :return: 请求并保存成功，则返回图片在本机的相对保存地址。否则返回None
        """
        if img_url in img_url2relativePath_dict:  # 检查此图片是否之前下载过
            return img_url2relativePath_dict[img_url]

        img_type = img_url.split(".")[-1]
        if img_type.lower() not in ["jpg", "png", "gif"]:
            print("----------------", img_url)
            return None
        try:
            r = requests.get(img_url, timeout=5, stream=True, headers=request_header)  # 请求图片
        except Exception as e:
            print("--------: ", img_url)
            traceback.print_exc()
            return None

        if r.status_code == 200:
            try:
                img_relative_path = os.path.join("renmin_data", "imgs",
                                                 f"{uuid.uuid4()}.{img_type}")  # 保存图片，获得图片保存的相对地址
                with open(os.path.join(PARENT_DIR, img_relative_path), 'wb') as f:
                    f.write(r.content)  # 将内容写入图片
                print("success download imgs: ", img_relative_path)
                img_url2relativePath_dict[img_url] = img_relative_path
                return img_relative_path
            except Exception as e:
                print("图片保存失败！ " + str(e))
                return None
            finally:
                del r
        return None

    for img_url in imgs:
        time.sleep(1)
        img_relative_path_ = download_img(img_url)
        if img_relative_path_ is not None:
            imgs_saved_path.append(img_relative_path_)

    with open(os.path.join(PARENT_DIR, "renmin_data", "img_url2relativePath_dict.json"), 'w', encoding='utf-8') as f:
        json.dump(img_url2relativePath_dict, f)

    return ariticle_content, imgs_saved_path



def get_article_contentAndImgs_by_url():
    spidered_data_name = []
    for json_path in Path(os.path.join(PARENT_DIR, "renmin_data", "article_data")).iterdir():
        spidered_data_name.append(json_path.name.replace(json_path.suffix, ""))
    for json_path in tqdm(Path(os.path.join(PARENT_DIR, "renmin_data", "category_url_data")).iterdir()):  # 遍历所有种类文章的URL
        # time.sleep(1)
        article_dict = {}
        article_dict["title"] = []  # 每篇文章标题
        article_dict["content"] = []  # 每篇文章内容
        article_dict["imgs"] = []  # 每篇文章中的图片，用;分隔
        df_name = json_path.name.replace(json_path.suffix, "")
        if df_name in spidered_data_name:
            continue
        with open(json_path, "r", encoding='utf-8') as f:
            category_json = json.load(f)
        for url, title in category_json.items():
            docurl = url
            article_content, imgs_saved_path = deal_article_url_data(docurl)  # 获取每个文章的文本内容，以及其中的图片
            if article_content == "":
                continue
            article_dict["title"].append(title)
            article_dict["content"].append(article_content)
            article_dict["imgs"].append(";".join(imgs_saved_path))
        pd.DataFrame(article_dict).to_excel(os.path.join(PARENT_DIR, "renmin_data", "article_data", f"{df_name}.xlsx"),
                                            index=False)  # 按类别保存每种文章信息
        print(1)


if __name__ == "__main__":
    # 获取url
    # spider_category_data()
    # deal_article_url_data()
    get_article_contentAndImgs_by_url()