#!/usr/bin/env python
# coding: utf-8

# 本文件将互联网上爬取来的文章（包含图片），通过NLP工具（LAC）对其进行NER标注处理，最终生成NE字典文件，标注好的训练数据

# In[8]:


import numpy as np
import pandas as pd
import json
from pathlib import Path

from itertools import groupby
import matplotlib.pyplot as plt


# In[7]:


from LAC import LAC
lac = LAC(mode='lac')


# In[2]:


import re
def cut_sent(para):
    para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    return para.split("\n")


# ### 加载数据，包括Excel文件及其对应图片文件

# In[3]:


renmin_data_path_dir = "./renmin_data"
wangyi_data_path_dir = "./wangyi_data"
# renmin_fileName2df = {filePath.name.strip(filePath.suffix):pd.read_excel(filePath) for filePath in Path(f"{renmin_data_path_dir}/article_data").iterdir() if filePath.is_file()}
# wangyi_fileName2df = {filePath.name.strip(filePath.suffix):pd.read_excel(filePath) for filePath in Path(f"{wangyi_data_path_dir}/article_data").iterdir() if filePath.is_file()}


# In[76]:


# 查看文章总数
count = 0
# for name, df in renmin_fileName2df.items():
#     print(name, ":", df.shape)
#     count += df.shape[0]
# print("人民日报文章总数：---------", count, "\n")
#
# count = 0
# for name, df in wangyi_fileName2df.items():
#     print(name, ":", df.shape)
#     count += df.shape[0]
# print("网易文章总数：---------", count)


# In[4]:


test_content = "6月11日\n，江苏天制环保科技有限公司(下称“天制环保科技公司”)向中华慈善总会捐赠天制垃圾无氧裂解热气化处理设备仪式在北京举行。中华慈善总会会长宫蒲光，荣誉副会长、新闻界慈善促进会执行会长兼秘书长徐镱轩，天制环保科技公司董事长孙文明、总经理霍玉琪出席捐赠仪式。仪式上，天制环保科技公司向中华慈善总会捐赠了价值5000万元的无氧裂解垃圾热气化处理设备，将用于乡村垃圾处理与环境治理。 宫蒲光对天制环保科技公司的慷慨善举表示衷心感谢与诚挚的敬意。他指出，践行社会责任是企业提升自身价值与产品口碑的良好途径。天制环保科技公司与中华慈善总会的合作就是巩固拓展脱贫攻坚成果与乡村振兴有效衔接的一次积极尝试，通过企业向广大农村地区捐赠垃圾处理环保设备，将与中华慈善总会“幸福家园”村社互助工程共同为助力乡村振兴事业添砖加瓦。双方将通过在全国范围内进行试点推广，发展一批适合各地特点的农业农村集体企业，促进县域经济，提升农村农业高质量发展。 徐镱轩在讲话中表示，垃圾治理是环境保护的重要环节，是助力乡村振兴的重要手段，也是中华慈善总会广泛开展“幸福家园”村社互助工程的重要利器。天制环保科技公司是一家积极履行社会责任的企业，其研发的垃圾处理设备既能使农村垃圾得到彻底治理，改善美化农村环境，又能变废为宝，使垃圾转变为电能热能服务社会，为乡村农产品深加工提供绿色廉价能源，助力乡村振兴战略。 孙文明在接受《慈善公益报》记者采访时表示，天制垃圾无氧裂解热气化处理设备安装之后，首先解决了农村环保问题。天制垃圾无氧裂解热气化处理系统是目前国内最适合县域农村环境治理的垃圾处理系统，可实现垃圾无害化和资源化再利用，转化为电能和热能，进一步为乡村集体企业提供大棚供暖，蔬菜和食用菌的种植、烘干等，成为促进农村农民增收，践行美丽中国环保理念的有益实践。"
# 装载LAC模型
def article_label(article_content = test_content):
    """
        采用LAC工具对文章内容article_content进行标注，同时返回
    """
    def convert_word_to_train_char(w, tag):
        res = []
        if w == "\n" or w == "。" or w == "！" or w == "？":
            res.append("\n")
            return res
        for i, char in enumerate(w):
            if tag.lower() == "o":
                res.append(f"{char} O")
            else:
                if i == 0:
                    res.append(f"{char} B-{tag.upper()}")
                else:
                    res.append(f"{char} I-{tag.upper()}")
        return res
    labeled_content_list = []
    type2entity = {}
    
    # 先将文档进行分句
    sentences = cut_sent(article_content)
    
    lac_result = lac.run(sentences)
    for sen_tag in lac_result:
        for word, label in zip(sen_tag[0], sen_tag[1]):
            if label in ["ORG","PER", "TIME", "LOC"]:
                type2entity.setdefault(label, [])
                type2entity[label].append(word)
                labeled_content_list.extend(convert_word_to_train_char(word, label))
            else:
                labeled_content_list.extend(convert_word_to_train_char(word, "O"))
        labeled_content_list.append("\n")
    return type2entity, labeled_content_list
# article_label()


# In[82]:


# list(renmin_fileName2df.values())[0].head(1)


# In[ ]:





# In[ ]:


# 人民日报数据 将原始数据进行转化成可训练数据，同时统计相关数据
# all_type2entity = {}  # 实体未去重
# all_labeled_content_list = []
# all_entity2imgs = {}
# for name, df in renmin_fileName2df.items():
#     if df.shape[0] != 0:
#         for i,row in df.iterrows(): # 每篇文章
#             row_dic = row.dropna().to_dict()
#             imgs = row_dic.get('imgs', "")
#             # 分割提取图片
#             img_list = []
#             for img_path in imgs.split(";"):
#                 if len(img_path) > 0:
#                     img_list.append(img_path)
#
#             # 文章内容
#             content = row_dic.get("content", "")
#             type2entity, labeled_content_list = article_label(str(content)) # labeled_content_list:["X O", "D B-ORG", ...]
#             for type_, entities in type2entity.items():
#                 all_type2entity.setdefault(type_, [])
#                 all_type2entity[type_].extend(entities)
#
#                 # 为每个实体存储对应图片关系
#                 for entity in entities:
#                     all_entity2imgs.setdefault(entity, [])
#                     all_entity2imgs[entity].extend(img_list)
#
#             # 保存每个文章转化后的训练数据
#             all_labeled_content_list.append("\n".join(labeled_content_list))


# In[ ]:


# print(len(all_type2entity), len(all_labeled_content_list), len(all_entity2imgs))


# In[ ]:


# 网易数据 
# for name, df in wangyi_fileName2df.items():
#     if df.shape[0] != 0:
#         for i,row in df.iterrows(): # 每篇文章
#             row_dic = row.dropna().to_dict()
#             imgs = row_dic.get('imgs', "")
#             # 分割提取图片
#             img_list = []
#             for img_path in imgs.split(";"):
#                 if len(img_path) > 0:
#                     img_list.append(img_path)
#
#             # 文章内容
#             content = row_dic.get("content", "")
#             type2entity, labeled_content_list = article_label(str(content)) # labeled_content_list:["X O", "D B-ORG", ...]
#             for type_, entities in type2entity.items():
#                 all_type2entity.setdefault(type_, [])
#                 all_type2entity[type_].extend(entities)
#
#                 # 为每个实体存储对应图片关系
#                 for entity in entities:
#                     all_entity2imgs.setdefault(entity, [])
#                     all_entity2imgs[entity].extend(img_list)
#
#             # 保存每个文章转化后的训练数据
#             all_labeled_content_list.append("\n".join(labeled_content_list))
#
#
# # In[ ]:
#
#
# print(len(all_type2entity), len(all_labeled_content_list), len(all_entity2imgs))  # 未去重


# In[ ]:





# In[ ]:


# all_entity2imgs 中的图片可能具有重复，对其进行统计， 排序（多到少）,去重
# new_all_entity2imgs = {}
# count_list = {}
# for entity, imgs in all_entity2imgs.items():
#     if len(imgs) != len(set(imgs)):
#         temp = []
#         imgs_sorted = sorted(imgs)
#         for k, g in groupby(imgs_sorted):
#             temp.append((k, len(list(g))))
#         temp_sorted = [img for img, count in sorted(temp, key=lambda x: x[1], reverse = True)]
#         new_all_entity2imgs[entity] = temp_sorted[20:]  # 出现次数较高的前几个图片大多为无意义通用图片（如图标，logo等）
#     else:
#         new_all_entity2imgs[entity] = imgs
#     count_list[entity] = len(new_all_entity2imgs[entity])
# # sorted(count_list.items(), key=lambda x: x[1], reverse=True)
# all_entity2imgs = new_all_entity2imgs


# In[ ]:


# all_entity2imgs["黄河"]


# In[ ]:


# 文件保存
def save_json_file(file_path, data):
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
# save_json_file("./produced_data/all_type2entity.json", all_type2entity)
# save_json_file("./produced_data/all_labeled_content_list.json", all_labeled_content_list)
# save_json_file("./produced_data/all_entity2imgs.json", all_entity2imgs)


# In[ ]:





# In[ ]:

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 集成训练数据，同统计句子长度
all_labeled_content_list = read_json_file("./produced_data/all_labeled_content_list.json")
# 将所有数据拼接生成最终数据集
with open("./produced_data/all_data.txt", 'w', encoding='utf-8') as f:
    f.write("\n\n".join(all_labeled_content_list))

all_data = []
len_list = []
split_pattern = re.compile("[\n]{2,}")
for article_labeled_content in all_labeled_content_list:
    sentence_tag_list = split_pattern.split(article_labeled_content)
    for sentence_tag in sentence_tag_list:
        if len(sentence_tag) != 0:
            len_list.append(int((len(sentence_tag)/3)))
temp = sorted(len_list)
# 聚类统计
key2count = {}
for key, group in groupby(temp):
    key2count[str(key)] = len(list(group))
del key2count["1"]
del key2count["2"]
del key2count["3"]

data_visible = {}
temp = []
start = 0
for i, (k ,v) in enumerate(key2count.items()):
    if i == 0:
        start = k
        temp.append(v)
    else:
        if i % 10 == 0 or i == len(key2count) - 1:
            data_visible[(start, k)] = sum(temp)
            temp = []
            start = k
        else:
            temp.append(v)

plt.pie(labels = list(data_visible.keys()), x = list(data_visible.values()))
plt.show()
# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




