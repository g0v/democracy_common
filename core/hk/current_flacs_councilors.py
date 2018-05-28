#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import utils


sleep_second = 3
election_year = '2015'
election_ids = {
    '2015': 'Q19019115',
    '2011': 'Q5895284'
}
election_id = election_ids[election_year]
ad = 5
year_range = {5: '2016~2019', 4: '2012~2015'}[ad]
term_start = {5: '2016-01-01', 4: '2012-01-01'}[ad]
year, month, day = [int(x) for x in term_start.split('-')]
term_start_target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')

parties_path = 'hk/data/party_maps.json'
parties = json.load(open(parties_path))
cities_path = 'hk/data/cities_maps.json'
if os.path.isfile(cities_path):
    cities = json.load(open(cities_path))
else:
    cities = json.load(open('hk/data/city_en_zh.json'))
    cities = {x['itemLabel']: {
        'id': x['item'].split('/')[-1],
        'en': x['itemLabel_en'],
        'zh': x['itemLabel_zh']
    } for x in cities}
people_path = 'hk/data/flacs_councilor.json'
people = json.load(open(people_path))

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = defaultdict(list)
threshold = 4

for i, person in enumerate(people):
    person['election_year'] = election_year
    if len(areas[person['county']]) > threshold:
        continue
    print(person['name'])
    item = utils.person_page_item_hk(person)
    print(item.id)
    areas[person['county']].append(item.id)
    people[i]['wikidata_qid'] = item.id

    labels = {}
    for code in ['zh', 'zh-tw', 'zh-hant']:
        labels[code] = person['name']
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

    # term
    term_id = cities[person['county']]['councilor_terms'][str(ad)]
    term_target = pywikibot.ItemPage(repo, term_id)
    # term_start
    if person.get('term_start'):
        term_start_year, term_start_month, term_start_day = [int(x) for x in person['term_start'].split('-')]
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
        if not person.get('special_constituency'):
            electoral_area_title = '%s%s區議員選區' % (person['county'], person['town'])
        else:
            electoral_area_title = '%s當然議員' % person['county']
        item_id = utils.get_qnumber(wikiarticle=electoral_area_title, lang="zh")
        target = pywikibot.ItemPage(repo, item_id)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)
    json.dump(people, open(people_path, 'w'), indent=2, ensure_ascii=False)
