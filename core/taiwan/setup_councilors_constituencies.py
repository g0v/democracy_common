#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot
from pywikibot import pagegenerators as pg

from common import db_settings, utils


conn = db_settings.con_councilor()
c = conn.cursor()

overwrite = True

c.execute('''
    select row_to_json(_)
    from (
        select county, constituency, district, county || '議員第' || constituency || '選舉區' as electoral_area_title
        from candidates_terms
        Where election_year = '2014'
        group by county, constituency, district
        order by county, constituency
    ) _
''')

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

wiki_maps_path = 'taiwan/data/city_councils_councilor_maps.json'
if os.path.isfile(wiki_maps_path):
    wiki_maps = json.load(open(wiki_maps_path))
#else:
#    query = '''
#        SELECT ?council ?councilLabel ?city ?cityLabel ?councilor_position ?councilor_positionLabel WHERE {
#            ?council wdt:P31 wd:Q3308596;
#                wdt:P17 wd:Q865;
#                wdt:P1001 ?city;
#                wdt:P527 ?councilor_position.
#            SERVICE wikibase:label { bd:serviceParam wikibase:language "zh-tw". }
#        }
#    '''
#    generator = pg.WikidataSPARQLPageGenerator(query, site=wikidata_site)
#    query_result = [item for item in generator]
#    json.dump(query_result, open(wiki_maps_path, 'w'), indent=2, ensure_ascii=False)
for r in wiki_maps:
    break
    county_constituency_label = '%s議員選區' % r['cityLabel']
    if not r.get('county_constituency'):
        try:
            item_id = utils.get_qnumber(wikiarticle=county_constituency_label, lang="zh-tw")
            if not item_id:
                raise
        except:
            labels = {}
            for code in ['zh', 'zh-tw', 'zh-hant']:
                labels[code] = county_constituency_label
            item_id = utils.create_item(wikidata_site, labels)
    else:
        item_id = r['county_constituency']
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    print(county_constituency_label, item.id)

    # 性質
    try:
        if 'Q49924492' not in [x.target.id for x in item.claims['P279']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q49924492') # Q49924492 縣市議員選區
        claim.setTarget(target)
        item.addClaim(claim)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 中華民國
        claim.setTarget(target)
        item.addClaim(claim)

    # 管轄區域
    try:
        item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        county_target = pywikibot.ItemPage(wikidata_site, r['city'].split('/')[-1])
        claim.setTarget(county_target)
        item.addClaim(claim)

    # of
    try:
        item.claims['P642']
    except:
        claim = pywikibot.Claim(repo, 'P642')
        county_target = pywikibot.ItemPage(wikidata_site, r['council'].split('/')[-1])
        claim.setTarget(county_target)
        item.addClaim(claim)

    r['county_constituency'] = item_id
    r['county_constituencyLabel'] = county_constituency_label
json.dump(wiki_maps, open(wiki_maps_path, 'w'), indent=2, ensure_ascii=False)

for row in c.fetchall()[110:]:
    r = row[0]
    print(r['county'])
    try:
        item_id = utils.get_qnumber(wikiarticle=r['electoral_area_title'], lang="zh-tw")
        if not item_id:
            raise
    except:
        labels = {}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            labels[code] = r['electoral_area_title']
        item_id = utils.create_item(wikidata_site, labels)
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    print(r['electoral_area_title'], item.id)

    # labels & description & aliases
    data = defaultdict(dict)
    labels, descriptions = r['electoral_area_title'], r['district']
    for code in ['zh', 'zh-tw', 'zh-hant']:
        if item.labels.get(code, '') != labels:
            data['labels'][code] = labels
        if item.descriptions.get(code, '') != descriptions:
            data['descriptions'][code] = descriptions
    if bool(data):
        item.editEntity(data, asynchronous=False)
    if not item.aliases.get('zh-hant'):
        ref = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']
        aliases_label = []
        for x in [ref[r['constituency']-1], '%d' % r['constituency'], '%02d' % r['constituency']]:
            for y in ['選舉區', '選區']:
                aliases_label.append("%s議員第%s%s" % (r['county'], x, y))
                print("%s議員第%s%s" % (r['county'], x, y))
        for code in ['zh', 'zh-tw', 'zh-hant']:
            aliases_exist = item.aliases.get(code, [])
            aliases_not_exist = [alias for alias in aliases_label if alias not in aliases_exist]
            data['aliases'][code] = aliases_exist + aliases_not_exist
        item.editEntity(data, asynchronous=False)

    # electoral area

    for f in wiki_maps:
        if f['cityLabel'] == r['county']:
            r['city'] = f['city'].split('/')[-1]
            r['county_constituency'] = f['county_constituency']
            break

    # 性質
    if r.get('county_constituency'):
        try:
            if r['county_constituency'] not in [x.target.id for x in item.claims['P31']]:
                item.removeClaims(item.claims['P31'])
                raise
        except:
            claim = pywikibot.Claim(repo, 'P31')
            target = pywikibot.ItemPage(repo, r['county_constituency']) # 該縣市議員選區
            claim.setTarget(target)
            item.addClaim(claim)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 中華民國
        claim.setTarget(target)
        item.addClaim(claim)

    # 管轄區域
    try:
        item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        if not r.get('city'):
            county_page = pywikibot.Page(site, r['county'])
            try:
                county_target = pywikibot.ItemPage.fromPage(county_page)
            except:
                county_q = utils.get_qnumber(wikiarticle=r['county'], lang="zh-tw")
                county_target = pywikibot.ItemPage(wikidata_site, county_q)
        else:
            county_target = pywikibot.ItemPage(wikidata_site, r['city'])
        claim.setTarget(county_target)
        item.addClaim(claim)
