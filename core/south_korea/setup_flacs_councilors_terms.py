#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot

from common import utils


election_year = '2014'
sleep_second = 5
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

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

for county, v in cities.items():
    print(county)
    # 의원동정 議員
    try:
        ad = utils.get_korea_flacs_councilor_term_ad(county, election_year)
    except:
        continue
    term_name = '제%d대 %s 의원동정' % (ad, county)

    if not cities[county].get('councilor_terms', {}).get(ad):
        try:
            item_id = utils.get_qnumber(wikiarticle=term_name, lang='ko')
            if not item_id:
                raise
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if item.labels['ko'] != term_name:
                raise
        except:
            labels = {'ko': term_name, 'en': '%s Councilor in %s' % (utils.ordinal_number(ad), cities[county]['en'])}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                labels[code] = '第%d屆%s議員' % (ad, cities[county]['zh'])
            item_id = utils.create_item(wikidata_site, labels)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
        if cities[county].get('terms'):
            cities[county]['councilor_terms'][ad] = item.id
        else:
            cities[county]['councilor_terms'] = {ad: item.id}
    else:
        item_id = cities[county]['councilor_terms'][ad]
        item = pywikibot.ItemPage(repo, item_id)
        item.get()
    print(term_name, item.id)

    # descriptions
    if not item.descriptions.get('ko'):
        end_year = utils.get_korea_flacs_councilor_term_ad(county, election_year, get_end_year=True)
        year_range = '%s~%s' % (election_year, end_year)
        descriptions = {'ko': '%s %s 의원동정' % (year_range, county), 'en': '%s Councilor in %s' % (year_range, cities[county]['en'])}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            descriptions[code] = '%s %s議員' % (year_range, cities[county]['zh'])
        item.editDescriptions(descriptions, asynchronous=False)

    # terms

    # 性質
    try:
        for claim in item.claims['P31']:
            if claim.target.id == 'Q15238777':
                break
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q15238777') # Q15238777 legislative term
        claim.setTarget(target)
        item.addClaim(claim)

    # 關於
    try:
        claim.qualifiers['P642']
    except:
        qualifier = pywikibot.Claim(repo, 'P642')
        target = pywikibot.ItemPage(wikidata_site, cities[county]['council'])
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # 系列序號
    try:
        claim.qualifiers['P1545']
    except:
        qualifier = pywikibot.Claim(repo, 'P1545')
        qualifier.setTarget(str(ad))
        claim.addQualifier(qualifier)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q884') # Q884 South Korea
        claim.setTarget(target)
        item.addClaim(claim)

    # 管轄區域
    try:
        item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        target = pywikibot.ItemPage(repo, cities[county]['id'])
        claim.setTarget(target)
        item.addClaim(claim)

    # start_at
    try:
        item.claims['P571']
    except:
        claim = pywikibot.Claim(repo, 'P571')
        year, month, day = int(election_year), 7, 1
        target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
        claim.setTarget(target)
        item.addClaim(claim)

#   # end_at
#   try:
#       item.claims['P576']
#   except:
#       claim = pywikibot.Claim(repo, 'P576')
#       year, month, day = utils.get_korea_flacs_councilor_term_ad(county, election_year, get_end_year=True), '07', '01'
#       target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
#       claim.setTarget(target)
#       item.addClaim(claim)
json.dump(cities, open(cities_path, 'w'), indent=2, ensure_ascii=False, sort_keys=True)
