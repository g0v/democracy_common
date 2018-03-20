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
    councils = {x['itemLabel']: x['item'].split('/')[-1] for x in councils}

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
for county, v in cities.items():
    print(county)
    try:
        if not v.get('council'):
            council_name = '%s의회' % county
            cities[county]['council'] = councils[county]
            council_item = pywikibot.ItemPage(repo, councils[council_name])
        else:
            council_item = pywikibot.ItemPage(repo, v['council'])
    except:
        continue
    county_target = pywikibot.ItemPage(repo, v['id'])

    # councilor position
    if not v.get('councilor_position'):
        position = '%s의원동정' % county
        try:
            match = False
            for q_id in utils.get_qnumber(wikiarticle=position, lang="ko", limit=None):
                position_item = pywikibot.ItemPage(repo, q_id)
                position_item.get()
                if position_item.claims.get('P31') and 'Q4164871' in [x.target.id for x in position_item.claims['P31']]: # Q4164871 職位
                    match = True
                    break
            if not match:
                raise
        except:
            position_labels = {'ko': position, 'en': '%s councilor' % v['en']}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                position_labels[code] = '%s議員' % v['zh']
            position_item_id = utils.create_item(wikidata_site, position_labels)
            position_item = pywikibot.ItemPage(repo, position_item_id)
            position_item.get()
            print('new position page created.')
    else:
        position_item = pywikibot.ItemPage(repo, v['councilor_position'])
        position_item.get()
    print(position, position_item.id)
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
        target = pywikibot.ItemPage(repo, 'Q884') # Q884 South Korea
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
    labels = {'en': '%s municipal council' % v['en']}
    for code in ['zh', 'zh-tw', 'zh-hant']:
        labels[code] = '%s廣域自治議會' % v['zh']
    council_item.editLabels(labels, asynchronous=False)

    if not council_item.aliases.get('zh'):
        aliases = {'en': ['%s FLACS council' % v['en']]}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            aliases[code] = ['%s一級縣市議會' % v['zh']]
        council_item.editAliases(aliases, asynchronous=False)

    # 性質
    try:
        if 'Q37002670' not in [x.target.id for x in council_item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q37002670') # Q37002670 一院制
        claim.setTarget(target)
        council_item.addClaim(claim)
    try:
        if 'Q3308596' not in [x.target.id for x in council_item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q3308596') # Q3308596 市長－議會制
        claim.setTarget(target)
        council_item.addClaim(claim)

    # 國家
    try:
        council_item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q884') # Q884 South Korea
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
