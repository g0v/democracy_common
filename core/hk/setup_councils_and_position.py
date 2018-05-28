#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import utils


# below query could generate hk/data/city_ko_en_zh.json
'''
select ?item ?itemLabel ?itemLabel_en where {
  ?item wdt:P31 wd:Q50256.
optional{
  ?item wdt:P31 wd:Q50256.
  ?item rdfs:label ?itemLabel_en .
filter(lang(?itemLabel_en)='en')
}
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
}
'''
cities_path = 'hk/data/cities_maps.json'
if os.path.isfile(cities_path):
    cities = json.load(open(cities_path))
else:
    cities = json.load(open('hk/data/city_en_zh.json'))
    cities = {x['itemLabel']: {
        'id': x['item'].split('/')[-1],
        'en': x['itemLabel_en'],
        'zh': x['itemLabel']
    } for x in cities}

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
for county, v in cities.items():
    print(county)
    try:
        if not v.get('council'):
            council_name = '%s議會' % county
            page = pywikibot.Page(site, council_name)
            council_item = pywikibot.ItemPage.fromPage(page)
            continue
        else:
            council_item = pywikibot.ItemPage(repo, v['council'])
    except:
        council_name = '%s區議會' % county
        page = pywikibot.Page(site, council_name)
        council_item = pywikibot.ItemPage.fromPage(page)
        cities[county]['council'] = council_item.id
        continue
    county_target = pywikibot.ItemPage(repo, v['id'])
    # county P194 -> council
    try:
        county_target.claims['P194']
    except:
        claim = pywikibot.Claim(repo, 'P194')
        claim.setTarget(council_item)
        county_target.addClaim(claim)

    # councilor position
    if not v.get('councilor_position'):
        position = '%s議員' % county
        try:
            match = False
            for q_id in utils.get_qnumber(wikiarticle=position, lang="zh", limit=None):
                position_item = pywikibot.ItemPage(repo, q_id)
                position_item.get()
                if position_item.claims.get('P31') and 'Q4164871' in [x.target.id for x in position_item.claims['P31']]: # Q4164871 職位
                    match = True
                    break
            if not match:
                raise
        except:
            position_labels = {'en': '%s councilor' % v['en']}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                position_labels[code] = position
            position_item_id = utils.create_item(wikidata_site, position_labels)
            position_item = pywikibot.ItemPage(repo, position_item_id)
            position_item.get()
            print('new position page created.')
    else:
        position_item = pywikibot.ItemPage(repo, v['councilor_position'])
        position_item.get()
    print(position_item, position_item.id)
    cities[county]['councilor_position'] = position_item.id

    # 性質
    try:
        if 'Q4164871' not in [x.target.id for x in position_item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q4164871') # Q4164871 職位
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 上級分類
    try:
        position_item.claims['P279']
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q708492') # Q708492 縣市議員
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 屬於
    try:
        position_item.claims['P361']
    except:
        claim = pywikibot.Claim(repo, 'P361')
        claim.setTarget(council_item)
        position_item.addClaim(claim)

    # 國家
    try:
        position_item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q148') # Q148 China
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 管轄區域
    try:
        position_item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        claim.setTarget(county_target)
        position_item.addClaim(claim)

    # councils
    labels = {'en': '%s Council' % v['en']}
    for code in ['zh', 'zh-tw', 'zh-hant']:
        labels[code] = '%s議會' % v['zh']
    council_item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        if 'Q836365' not in [x.target.id for x in council_item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q836365') # Q836365 香港區議會
        claim.setTarget(target)
        council_item.addClaim(claim)

    # 國家
    try:
        council_item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q148') # Q148 China
        claim.setTarget(target)
        council_item.addClaim(claim)

    # 管轄區域
    try:
        council_item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        claim.setTarget(county_target)
        council_item.addClaim(claim)

    # 子類
    try:
        council_item.claims['P527']
    except:
        claim = pywikibot.Claim(repo, 'P527')
        claim.setTarget(position_item)
        council_item.addClaim(claim)
json.dump(cities, open(cities_path, 'w'), indent=2, ensure_ascii=False, sort_keys=True)
