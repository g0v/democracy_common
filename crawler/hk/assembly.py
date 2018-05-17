# -*- coding: utf-8 -*-
import re
import scrapy


class Spider(scrapy.Spider):
    name = "assembly"
    allowed_domains = ["legco.gov.hk"]
    start_urls = ["https://www.legco.gov.hk/general/chinese/members/yr16-20/biographies.htm",]
    download_delay = 1

    def parse(self, response):
        for node in response.css('.bio-member-detail a::attr(href)').extract():
            yield response.follow(node, callback=self.parse_detail)

    def parse_detail(self, response):
        item = {}
        item['name'] = response.xpath(u'//p[re:test(., "選舉組別")]/preceding-sibling::h2/text()').re_first(u'(.*?)議員')
        m = re.search(u'(?P<type>(功能界別|地方選區))\s*[-–]\s*(?P<detail>.*)', response.xpath(u'//p[re:test(., "選舉組別")]/following-sibling::ul/li/text()').extract_first())
        if m.group('type') == u'地方選區':
            item['county'] = m.group('detail').strip()
        else:
            item['category'] = m.group('detail').replace(u'(', u'（').replace(u')', u'）').strip()
        item['party'] = response.xpath(u'//p[re:test(., "所屬政治團體")]/following-sibling::ul/li/text()').extract_first()
        item['party'] = item['party'].strip() if item['party'] else item['party']

        item['career'] = response.xpath(u'//p[re:test(., "職業")]/following-sibling::ul/li/text()').extract_first()
        item['career'] = item['career'].strip() if item['career'] else item['career']
        item['email'] = response.xpath(u'//td[re:test(., "電郵")]/following-sibling::td/a/text()').extract_first()
        yield item

