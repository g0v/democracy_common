#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot

from common import utils


cities = json.load(open('south_korea/data/city_ko_en_zh.json'))
cities = {x['itemLabel']: {
    'id': x['item'].split('/')[-1],
    'en': x['itemLabel_en'],
    'zh': x['itemLabel_zh']
} for x in cities}
people = json.load(open('south_korea/data/assembly_people.json'))

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = set()
for x in people:
    if x['type'] == 'region':
        if x['county'] != x['constituency']:
            areas.add('%s %s' % (x['county'], x['constituency']))
        else:
            areas.add('%s' % x['county'])
print(len(areas))
for i, area in enumerate(areas):
    print(i, area)
    county = area.split()[0]
    try:
        match = False
        for item_id in utils.get_qnumber(wikiarticle=area, lang="ko", limit=None):
            print(item_id)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if item.labels['ko'] == area and len(item.claims.get('P31', [])) == 1 and 'Q50240982' in [x.target.id for x in item.claims['P31']]:
                match = True
                break
        if not match:
            create = input('create new entity?(y/n)')
            if create == 'y':
                raise
    except:
        labels = {"ko": area}
        item_id = utils.create_item(wikidata_site, labels)
        item = pywikibot.ItemPage(repo, item_id)
        item.get()
    print(area, item.id)

    # description
    if not item.descriptions.get('ko'):
        descriptions = {'ko': '%s 국회의원 선거구' % area} # 국회의원 선거구 國會議員選舉區
        item.editDescriptions(descriptions, asynchronous=False)

    # electoral area

    # 性質
    try:
        if 'Q50240982' not in [x.target.id for x in item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q50240982') # Q50240982 南韓國會議員選舉區
        claim.setTarget(target)
        item.addClaim(claim)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q884') # Q884 South Korea
        claim.setTarget(target)
        item.addClaim(claim)

    # 所在行政區
    try:
        item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        county_page = pywikibot.Page(site, area.split()[0])
        try:
            county_target = pywikibot.ItemPage.fromPage(county_page)
        except:
            county_q = utils.get_qnumber(wikiarticle=area.split()[0], lang="zh-tw")
            county_target = pywikibot.ItemPage(wikidata_site, county_q)
        claim.setTarget(county_target)
        item.addClaim(claim)
