#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import utils


# below query could generate south_korea/data/city_ko_en_zh.json
'''
SELECT ?item ?itemLabel ?itemLabel_en ?itemLabel_zh WHERE {
  ?item wdt:P31/wdt:P279* wd:Q10864048 .
  ?item wdt:P17 wd:Q884 .
optional{
  ?item wdt:P31/wdt:P279* wd:Q10864048 .
  ?item wdt:P17 wd:Q884 .
  ?item rdfs:label ?itemLabel_en .
filter(lang(?itemLabel_en)='en')
}
optional{
  ?item wdt:P31/wdt:P279* wd:Q10864048 .
  ?item wdt:P17 wd:Q884 .
  ?item rdfs:label ?itemLabel_zh .
filter(lang(?itemLabel_zh)='zh-hant')
}
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ko". }
 }
'''
cities_path = 'south_korea/data/cities_maps.json'
if os.path.isfile(cities_path):
    cities = json.load(open(cities_path))
else:
    cities = json.load(open('south_korea/data/city_ko_en_zh.json'))
    cities = {x['itemLabel']: {
        'id': x['item'].split('/')[-1],
        'en': x['itemLabel_en'],
        'zh': x['itemLabel_zh']
    } for x in cities}
    # below query could generate south_korea/data/flacs_councils.json
    '''
    SELECT ?item ?itemLabel WHERE {
    VALUES ?councils {wd:Q4358176 wd:Q3154693}
    ?item wdt:P31 ?councils .
    ?item wdt:P17 wd:Q884
    SERVICE wikibase:label { bd:serviceParam wikibase:language "ko,[AUTO_LANGUAGE],en". }
    }
    '''
    councils = json.load(open('south_korea/data/flacs_councils.json'))
    councils = {re.sub('의회', '', x['itemLabel']): x['item'].split('/')[-1] for x in councils}
people = json.load(open('south_korea/data/flacs_councilor.json'))

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = defaultdict(lambda: {
    'seats': 0,
    'constituencies': {}
})
for x in people:
    areas[x['county']]['seats'] += 1
    if x['type'] == 'region':
        areas[x['county']]['constituencies'][x['constituency']] = x['town']
    elif x['type'] == 'proportion':
        areas[x['county']]['constituencies']['%s 비례대표 선거구' % x['constituency']] = x['county']
for county, v in areas.items():
    print(county)
    county_target = pywikibot.ItemPage(wikidata_site, cities[county]['id'])
    # county council legislature
    if not cities[county].get('council'):
        cities[county]['council'] = councils[county]
    council_item = pywikibot.ItemPage(repo, cities[county]['council'])
    council_item.get()
    # 席次
    try:
        council_item.claims['P1342']
    except:
        claim = pywikibot.Claim(repo, 'P1342')
        target = pywikibot.WbQuantity(site=site, amount=v['seats'])
        claim.setTarget(target)
        council_item.addClaim(claim)

    # 選舉區數量
    try:
        council_item.claims['P4253']
    except:
        claim = pywikibot.Claim(repo, 'P4253')
        target = pywikibot.WbQuantity(site=site, amount=len(v['constituencies']))
        claim.setTarget(target)
        council_item.addClaim(claim)

    # county council specific constituency
    if not cities[county].get('county_councilor_constituency'):
        county_constituency_label = '%s 의원동정 선거구' % county
        try:
            item_id = utils.get_qnumber(wikiarticle=county_constituency_label, lang="ko")
            if not item_id:
                raise
            county_constituency_item = pywikibot.ItemPage(repo, item_id)
            county_constituency_item.get()
            if county_constituency_item.labels['ko'] != county_constituency_label:
                raise
        except:
            labels = {"ko": county_constituency_label}
            item_id = utils.create_item(wikidata_site, labels)
            county_constituency_item = pywikibot.ItemPage(repo, item_id)
            county_constituency_item.get()
        cities[county]['county_councilor_constituency'] = county_constituency_item.id
    else:
        county_constituency_item = pywikibot.ItemPage(repo, cities[county]['county_councilor_constituency'])
        county_constituency_item.get()

    if not county_constituency_item.labels.get('zh'):
        labels = {'en': 'FLACS Council Constituency of %s' % cities[county]['en']}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            labels[code] = '%s廣域自治議員選區' % cities[county]['zh']
        county_constituency_item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        match = False
        for x in county_constituency_item.claims['P279']:
            if 'Q50258518' == x.target.id:
                claim = x
                match = True
                break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q50258518') # Q50258518 南韓縣市議員選區
        claim.setTarget(target)
        county_constituency_item.addClaim(claim)

    # of
    try:
        qualifier = claim.qualifiers['P642']
    except:
        qualifier = pywikibot.Claim(repo, 'P642')
        qualifier.setTarget(council_item)
        claim.addQualifier(qualifier)

    # 國家
    try:
        county_constituency_item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q884') # Q884 South Korea
        claim.setTarget(target)
        county_constituency_item.addClaim(claim)

    # 所在行政區
    try:
        claims = county_constituency_item.claims['P1001']
        county_constituency_item.removeClaims(claims)
    except:
        pass
    try:
        county_constituency_item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        claim.setTarget(county_target)
        county_constituency_item.addClaim(claim)


    #constituencies
    for constituency, town in v['constituencies'].items():
        try:
            item_id = utils.get_qnumber(wikiarticle=constituency, lang="ko")
            if not item_id:
                raise
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if not re.search(constituency, item.labels['ko'):
                raise
        except:
            labels = {"ko": constituency}
            create = input('create new constituency: %s ?(y/n)' % constituency)
            if create == 'y':
                item_id = utils.create_item(wikidata_site, labels)
                item = pywikibot.ItemPage(repo, item_id)
                item.get()
        print(constituency, item.id)

        # description
        if not item.descriptions.get('ko'):
            descriptions = {'ko': '%s 의회 선거구' % county} # 의원 선거구 議會選舉區
            item.editDescriptions(descriptions, asynchronous=False)

        # electoral area

        # 性質
        try:
            if county_constituency_item.id not in [x.target.id for x in item.claims['P31']]:
                raise
        except:
            claim = pywikibot.Claim(repo, 'P31')
            claim.setTarget(county_constituency_item)
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
            if re.search('비례대표', constituency):
                target = county_target
            else:
                page = pywikibot.Page(site, town)
                try:
                    target = pywikibot.ItemPage.fromPage(page)
                except:
                    q = utils.get_qnumber(wikiarticle=town, lang="zh-tw")
                    if q:
                        target = pywikibot.ItemPage(wikidata_site, q)
                    else:
                        target = county_target
            claim.setTarget(target)
            item.addClaim(claim)

json.dump(cities, open(cities_path, 'w'), indent=2, ensure_ascii=False, sort_keys=True)
