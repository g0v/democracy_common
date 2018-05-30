#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot

from common import utils


ad = 5
year_range = {5: '2016~2019', 4: '2012~2015'}[ad]
term_start = {5: '2016-01-01', 4: '2012-01-01'}[ad]
year, month, day = [int(x) for x in term_start.split('-')]
term_start_target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
# below query could generate hk/data/city_en_zh.json
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
    county_target = pywikibot.ItemPage(wikidata_site, cities[county]['id'])
    county_target.get()
    council_item = pywikibot.ItemPage(repo, cities[county]['council'])
    council_item.get()
    # HoG position
    if not v.get('HoG_position'):
        position = '%s民政事務專員' % county
        try:
            match = False
            for q_id in utils.get_qnumber(wikiarticle=position, lang="zh", limit=None):
                position_item = pywikibot.ItemPage(repo, q_id)
                position_item.get()
                if position_item.claims.get('P31') and 'Q294414' in [x.target.id for x in position_item.claims['P31']]: # Q294414 職位
                    match = True
                    break
            if not match:
                raise
        except:
            position_labels = {'en': 'district officer of %s' % v['en']}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                position_labels[code] = position
            position_item_id = utils.create_item(wikidata_site, position_labels)
            position_item = pywikibot.ItemPage(repo, position_item_id)
            position_item.get()
            print('new position page created.')
    else:
        position_item = pywikibot.ItemPage(repo, v['HoG_position'])
        position_item.get()
    print(position_item, position_item.id)
    cities[county]['HoG_position'] = position_item.id

    # office held by head of government
    try:
        county_target.qualifiers['P1313']
    except:
        claim = pywikibot.Claim(repo, 'P1313')
        claim.setTarget(position_item)
        county_target.addClaim(claim)

    # executive body
    try:
        county_target.qualifiers['P208']
    except:
        claim = pywikibot.Claim(repo, 'P208')
        claim.setTarget(council_item)
        county_target.addClaim(claim)

    # part of
    try:
        position_item.claims['P361']
    except:
        claim = pywikibot.Claim(repo, 'P361')
        claim.setTarget(council_item)
        position_item.addClaim(claim)

    # has part
    try:
        if position_item.id not in [x.target.id for x in item.claims['P527']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P527')
        claim.setTarget(position_item)
        council_item.addClaim(claim)

    # subclass of
    try:
        position_item.claims['P279']
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q11129049') # 民政事務專員
        claim.setTarget(target)
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
json.dump(cities, open(cities_path, 'w'), indent=2, ensure_ascii=False, sort_keys=True)
