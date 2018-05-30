#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import utils


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
people = json.load(open('hk/data/flacs_councilor.json'))

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = defaultdict(lambda: {
    'seats': 0,
    'constituencies': {}
})
for x in people:
    areas[x['county']]['seats'] += 1
    if not x.get('special_constituency'):
        areas[x['county']]['constituencies']['%s%s區議員選區' % (x['county'], x['town'])] = 'District Councils Constituency in %s, %s' % (x['town_en'], cities[x['county']]['en'])
    else:
        areas[x['county']]['constituencies']['%s當然議員' % x['county']] = 'Ex Officio Member in %s' % cities[x['county']]['en']
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
        county_constituency_label = '%s區議員選區' % county
        try:
            item_id = utils.get_qnumber(wikiarticle=county_constituency_label, lang="zh")
            if not item_id:
                raise
            county_constituency_item = pywikibot.ItemPage(repo, item_id)
            county_constituency_item.get()
            if county_constituency_item.labels['zh'] != county_constituency_label:
                raise
        except:
            labels = {"zh": county_constituency_label}
            item_id = utils.create_item(wikidata_site, labels)
            county_constituency_item = pywikibot.ItemPage(repo, item_id)
            county_constituency_item.get()
        cities[county]['county_councilor_constituency'] = county_constituency_item.id
    else:
        county_constituency_item = pywikibot.ItemPage(repo, cities[county]['county_councilor_constituency'])
        county_constituency_item.get()

    if not county_constituency_item.labels.get('en'):
        labels = {'en': 'Council Constituency of %s' % cities[county]['en']}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            labels[code] = county_constituency_label
        county_constituency_item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        match = False
        for x in county_constituency_item.claims['P279']:
            if 'Q54063790' == x.target.id:
                claim = x
                match = True
                break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q54063790') # Q54063790 香港區議會選區
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
        target = pywikibot.ItemPage(repo, 'Q148') # Q148 China
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
    for constituency, con_en in v['constituencies'].items():
        try:
            item_id = utils.get_qnumber(wikiarticle=constituency, lang="zh")
            if not item_id:
                raise
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if not re.search(constituency, item.labels['zh']):
                raise
        except:
            labels = {'en': con_en}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                labels[code] = constituency
            create = input('create new constituency: %s ?(y/n)' % constituency)
            if create == 'y':
                item_id = utils.create_item(wikidata_site, labels)
                item = pywikibot.ItemPage(repo, item_id)
                item.get()
        print(constituency, item.id)
        labels = {'en': con_en}
        item.editLabels(labels, asynchronous=False)

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
            target = pywikibot.ItemPage(repo, 'Q148') # Q148 China
            claim.setTarget(target)
            item.addClaim(claim)

        # 所在行政區
        try:
            item.claims['P131']
        except:
            claim = pywikibot.Claim(repo, 'P131')
            claim.setTarget(county_target)
            item.addClaim(claim)

json.dump(cities, open(cities_path, 'w'), indent=2, ensure_ascii=False, sort_keys=True)
