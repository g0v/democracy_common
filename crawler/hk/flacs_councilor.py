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
    name = "flacs_councilor"
    allowed_domains = ["districtcouncils.gov.hk"]
    start_urls = ["http://www.districtcouncils.gov.hk/",]
    download_delay = 1

    def __init__(self, ad=None, *args, **kwargs):
        super(Spider, self).__init__(*args, **kwargs)
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.driver = webdriver.Chrome("/var/chromedriver/chromedriver")

    def parse(self, response):
        for node in response.css('a.btn_district::attr(href)').extract():
            yield response.follow(node, callback=self.parse_district)

    def parse_district(self, response):
        self.driver.get(response.url)
        link = self.driver.find_element_by_xpath(u'//a[contains(., "區議員資料")]').get_attribute('href')
        yield response.follow(link, callback=self.parse_list)

    def parse_list(self, response):
        for node in response.css('.member_picCol').xpath('following-sibling::td/descendant::a/@href').extract():
            yield response.follow(node, callback=self.parse_profile)

    def parse_profile(self, response):
        item = {}
        item['county'] = re.sub(u'區區', u'區', response.css('.mySection').xpath('text()').re_first(u'(.*?)議會'))
        item['name'] = response.css('.member_name').xpath('text()').re_first(u'(.*?)(議員|女士|小姐|先生|博士|太平紳士)')
        term = re.search(u'(\d+)年(\d+)月(\d+)日', response.css('.member_name').xpath('text()').extract_first())
        if term:
            item['term_start'] = '%04d-%02d-%02d' % tuple([int(x) for x in term.groups()])
        item['town'] = re.sub('[-－]', '', response.xpath(u'//span[re:test(., "^選區$")]/parent::p[1]/text()').extract()[-1].strip())
        item['town'] = re.sub('\s*\(\S+\)', '', item['town'])
        item['special_constituency'] = response.xpath(u'//span[re:test(., "席位$")]/parent::p[1]/text()').re_first(u'當然議員')
        item['party'] = re.sub('-', '', response.xpath(u'//span[re:test(., "^所屬政治聯繫$")]/parent::p[1]/text()').extract()[-1].strip())
        item['email'] = response.xpath(u'//td[re:test(., "電郵地址")]/following-sibling::td/descendant::a/text()').extract_first()
        yield item
