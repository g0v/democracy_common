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

## Using query below to get taiwan/data/city_councils_councilor_maps.json
#    query = '''
#        SELECT ?council ?councilLabel ?city ?cityLabel ?councilor_position ?councilor_positionLabel WHERE {
#            ?council wdt:P31 wd:Q3308596;
#                wdt:P17 wd:Q865;
#                wdt:P1001 ?city;
#                wdt:P527 ?councilor_position.
#            SERVICE wikibase:label { bd:serviceParam wikibase:language "zh-tw". }
#        }
#    '''
wiki_maps_path = 'taiwan/data/city_councils_councilor_maps.json'
wiki_maps = json.load(open(wiki_maps_path))
for r in wiki_maps:
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
    if r.get('cityLabel_en'):
        city_item = pywikibot.ItemPage(repo, r['city'].split('/')[-1])
        city_item.get()
        city_label_en = city_item.labels['en']
    else:
        city_label_en = r.get('cityLabel_en')

    # English Labels
    labels = {'en': 'Constituency of Regional Councilors of %s' % city_label_en}
    if not item.labels.get('en'):
        item.editLabels(labels, asynchronous=False)
    data, aliases = defaultdict(dict), []
    if re.search('^臺', county_constituency_label):
        aliases.append(re.sub('^臺', '台', county_constituency_label))
    elif re.search('^台', county_constituency_label):
        aliases.append(re.sub('^台', '臺', county_constituency_label))
    if aliases:
        for code in ['zh', 'zh-tw', 'zh-hant']:
            aliases_exist = item.aliases.get(code, [])
            aliases_not_exist = [alias for alias in aliases if alias not in aliases_exist]
            data['aliases'][code] = aliases_exist + aliases_not_exist
        item.editEntity(data, asynchronous=False)

    # 性質
    try:
        match = False
        for x in item.claims['P279']:
            if 'Q49924492' == x.target.id:
                claim = x
                match = True
                break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q49924492') # Q49924492 縣市議員選區
        claim.setTarget(target)
        item.addClaim(claim)

    # of
    try:
        qualifier = claim.qualifiers['P642']
    except:
        qualifier = pywikibot.Claim(repo, 'P642')
        target = pywikibot.ItemPage(wikidata_site, r['council'].split('/')[-1])
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 Taiwan
        claim.setTarget(target)
        item.addClaim(claim)

    # 所在行政區
    try:
        claims = item.claims['P1001']
        item.removeClaims(claims)
    except:
        pass
    try:
        item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        county_target = pywikibot.ItemPage(wikidata_site, r['city'].split('/')[-1])
        claim.setTarget(county_target)
        item.addClaim(claim)

    r['cityLabel_en'] = city_label_en
    r['county_constituency'] = item_id
    r['county_constituencyLabel'] = county_constituency_label
json.dump(wiki_maps, open(wiki_maps_path, 'w'), indent=2, ensure_ascii=False)

'''
cec_councilors_constituency_path = 'taiwan/data/councilors_constituencies_2014_with_wikidata_id.json'
cec_maps = json.load(open(cec_councilors_constituency_path))
for row in c.fetchall():
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

    # get reference for electoralr_area and constituency_type

    for f in wiki_maps:
        if f['cityLabel'] == r['county']:
            r['city'] = f['city'].split('/')[-1]
            r['county_constituency'] = f['county_constituency']
            r['cityLabel_en'] = f['cityLabel_en']
            break

    for f in cec_maps:
        if f['wikidata_item'].split('/')[-1] == item.id:
            r['constituency_type'] = f['constituency_type']
            r['constituency_type_title'] = f['constituency_type_title']
            break

    # English Labels
    if not item.labels.get('en'):
        labels = {'en': '%s Constituency of Regional Councilors of %s' % (utils.ordinal_number(r['constituency']), r['cityLabel_en'])}
        item.editLabels(labels, asynchronous=False)

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

    # Right to vote
    if r['constituency_type'] == 'ethnical':
        try:
            item.claims['P2964']
        except:
            claim = pywikibot.Claim(repo, 'P2964')
            target = pywikibot.ItemPage(repo, utils.aborigine_id(r['constituency_type_title']))
            claim.setTarget(target)
            item.addClaim(claim)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 Taiwan
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
        '''
