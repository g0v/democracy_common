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
print(year, month, day)
input('..')
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
people = json.load(open('hk/data/flacs_councilor.json'))

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

for county, v in cities.items():
    print(county)
    term_name = '第%d屆%s議員' % (ad, county)

    if not cities[county].get('councilor_terms', {}).get(ad):
        try:
            item_id = utils.get_qnumber(wikiarticle=term_name, lang='zh')
            if not item_id:
                raise
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if item.labels['zh'] != term_name:
                raise
        except:
            labels = {'en': '%s Councilor in %s' % (utils.ordinal_number(ad), cities[county]['en'])}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                labels[code] = term_name
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
    if not item.descriptions.get('zh'):
        descriptions = {'en': '%s Councilor in %s' % (year_range, cities[county]['en'])}
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
        target = pywikibot.ItemPage(repo, 'Q148') # Q148 China
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
        claim.setTarget(term_start_target)
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
