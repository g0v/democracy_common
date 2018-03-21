# -*- coding: utf-8 -*-
from time import sleep
from random import randint
import re
import urllib
from urlparse import urljoin
import scrapy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display


class Spider(scrapy.Spider):
    name = "education_governor"
    allowed_domains = ["nec.go.kr"]
    start_urls = ["http://info.nec.go.kr/main/showDocument.xhtml?electionId=0000000000&topMenuId=EP&secondMenuId=EPEI01",]
    download_delay = 1

    def __init__(self, ad=None, *args, **kwargs):
        super(Spider, self).__init__(*args, **kwargs)
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.driver = webdriver.Chrome("/var/chromedriver/chromedriver")

    def parse(self, response):
        self.driver.get(response.url)
        assembly = self.driver.find_element_by_xpath('//a[@id="electionType4"]')
        assembly.click()
        sleep(randint(1, 2))
        election_ad = self.driver.find_elements_by_xpath('//select[@id="electionName"]/option')[1]
        election_ad.click()
        sleep(randint(1, 2))
        election = self.driver.find_element_by_xpath('//select[@id="electionCode"]/option[@value="11"]')
        election.click()
        sleep(randint(1, 2))
        submit = self.driver.find_element_by_xpath('//input[@id="searchBtn"]')
        submit.click()
        trs = self.driver.find_elements_by_css_selector('#table01 tbody tr')
        for i, tr in enumerate(trs):
            try:
                data = {}
                tds = [x.text for x in tr.find_elements_by_css_selector('td')[:4]]
                data['constituency'] = tds[0]
                data['name'], data['name_zh'] = re.sub(' ', '', tds[1]).split()
                data['name_zh'] = re.sub('[()]', '', data['name_zh'])
                data['gender'] = tds[2]
                data['birth'] = re.sub('\.', '-', tds[3].split()[0])
                yield data
            except Exception, e:
                print e
                print 'line %d' % i
                print tds
                raw_input()
