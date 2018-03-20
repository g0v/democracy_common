#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import utils


sleep_second = 3
election_year = '2014'
election_ids = {
    '2014': 'Q5518780',
    '2010': 'Q493454'
}
election_id = election_ids[election_year]

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
parties_path = 'south_korea/data/party_maps.json'
parties = json.load(open(parties_path))
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
people_path = 'south_korea/data/flacs_councilor.json'
people = json.load(open(people_path))

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = defaultdict(lambda: {
    'region': [],
    'proportion': []
})

for i, person in enumerate(people):
    threshold = 9 if person['type'] == 'region' else 0
    if len(areas[person['county']][person['type']]) > threshold:
        continue
    print(person['name'])
    item = utils.person_page_item_ko(person)
    print(item.id)
    people[i]['wikidata_qid'] = item.id
    areas[person['county']][person['type']].append(item.id)

    if not item.labels.get('zh'):
        labels = {}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            labels[code] = person['name_zh']
        item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        item.claims['P31']
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q5')
        claim.setTarget(target)
        item.addClaim(claim)

    # Q82955 政治人物
    try:
        if 'Q82955' not in [x.target.id for x in item.claims['P106']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P106')
        target = pywikibot.ItemPage(repo, 'Q82955')
        claim.setTarget(target)
        item.addClaim(claim)

    # 性別
    if person['gender']:
        try:
            item.claims['P21']
        except:
            claim = pywikibot.Claim(repo, 'P21')
            target = pywikibot.ItemPage(repo, utils.gender_id(person['gender']))
            claim.setTarget(target)
            item.addClaim(claim)

    # 生日
    if person['birth']:
        b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
        b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
        try:
            match = False
            if b_target not in [claim.target for claim in item.claims['P569']]:
                for claim in item.claims['P569']:
                    if claim.target.year == b_year:
                        claim.changeTarget(b_target)
                        match = True
                        break
            else:
                match = True
            if not match:
                raise
        except:
            claim = pywikibot.Claim(repo, 'P569')
            claim.setTarget(b_target)
            item.addClaim(claim)

    # term
    ad = utils.get_korea_flacs_councilor_term_ad(person['county'], election_year)
    term_id = cities[person['county']]['councilor_terms'][str(ad)]
    term_target = pywikibot.ItemPage(repo, term_id)
    # term_start
    term_start_year, term_start_month, term_start_day = int(election_year), 7, 1
    term_start_target = pywikibot.WbTime(year=term_start_year, month=term_start_month, day=term_start_day, precision='day')
    # XX縣市議員
    position_held_id = cities[person['county']]['councilor_position']
    try:
        match = False
        for i, x in enumerate(item.claims['P39']):
            if x.target.id == position_held_id:
                if len(x.qualifiers) == 0 or term_start_target == x.qualifiers['P580'][0].target:
                    claim = item.claims['P39'][i]
                    match = True
                    break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P39')
        target = pywikibot.ItemPage(repo, position_held_id)
        claim.setTarget(target)
        item.addClaim(claim)

    # start at
    try:
        claim.qualifiers['P580']
    except:
        qualifier = pywikibot.Claim(repo, 'P580')
        qualifier.setTarget(term_start_target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # 選舉於
    try:
        claim.qualifiers['P2715']
    except:
        qualifier = pywikibot.Claim(repo, 'P2715')
        target = pywikibot.ItemPage(repo, election_id)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # party
    if parties.get(person['party']):
        try:
            claim.qualifiers['P4100']
        except:
            qualifier = pywikibot.Claim(repo, 'P4100')
            target = pywikibot.ItemPage(repo, parties[person['party']])
            qualifier.setTarget(target)
            claim.addQualifier(qualifier)
            time.sleep(sleep_second)

    # terms
    try:
        claim.qualifiers['P2937']
    except:
        qualifier = pywikibot.Claim(repo, 'P2937')
        qualifier.setTarget(term_target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # constituency
    try:
        qualifier = claim.qualifiers['P768']
    except:
        qualifier = pywikibot.Claim(repo, 'P768')
        if person['type'] == 'region':
            electoral_area_title = person['constituency']
        elif person['type'] == 'proportion':
            electoral_area_title = '%s 비례대표 선거구' % person['constituency']
        item_id = utils.get_qnumber(wikiarticle=electoral_area_title, lang="ko")
        target = pywikibot.ItemPage(repo, item_id)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)
json.dump(people, open(people_path, 'w'), indent=2, ensure_ascii=False)
