# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     spider.py
   Description :
   Author :        sean
   date：          2017-12-02
-------------------------------------------------
   Change Activity:
                   2017-12-02: 上传到github by sean
-------------------------------------------------
"""

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pymongo
from config import *
import re

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

driver = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(driver, 10)

# PhantomJS默认窗口较小，改大点，设置为笔记本的分辨率
driver.set_window_size(1366, 768)


def search_and_first_page():
    driver.get("http://www.taobao.com")
    try:
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button"))
        )
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        input.send_keys(KEYWORD)
        submit.click()
        maxPage = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total"))
        )
        return (int(re.findall('\d+', maxPage.text)[0]))
    except TimeoutException as e:
        print('访问异常：', e)
        return search_and_first_page()


def next_page(pageNumber):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        input.clear()
        input.send_keys(pageNumber)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > ul > li.item.active > span"), str(pageNumber))
        )
    except TimeoutException as e:
        print("跳转页面异常：", e)
        return next_page(pageNumber)


def parse_date():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-itemlist .items .item")))
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('#mainsrp-itemlist .items .item')
    if items:
        for item in items:
            product = {
                'title': item.find(class_="row row-2 title").text.replace('\n', '').replace(' ', ''),
                'imageUrl': item.find('img')['data-src'],
                'price': float(item.find('strong').text),
                'serviceFree': item.find(class_="ship icon-service-free") is not None,
                'howManyPaid': int(item.find(class_="deal-cnt").text[:-3]),
                'shop': item.find(class_='shopname').text.strip(),
                'location': item.find(class_="location").text
            }
            if product: save_to_mongo(product)


def save_to_mongo(data):
    try:
        if db[MONGO_TABLE].insert_one(data):
            print('存储到MongoDB成功...', data)
    except Exception as e:
        print('存储到MongoDB失败...', e, data)


def main():
    try:
        # 首页加载及加载搜索第1页
        maxPage = search_and_first_page()
        pageNumber = 1
        print('**************正在解析第"{0}"页**************'.format(pageNumber))
        parse_date()

        # 循环加载剩余页
        for pageNumber in range(2, maxPage + 1):
            next_page(pageNumber)
            print('**************正在解析第"{0}"页**************'.format(pageNumber))
            parse_date()
    except Exception as e:
        print('出错啦...', e)
        driver.save_screenshot('screenshot.png')
    finally:
        driver.close()


if __name__ == '__main__':
    main()
