#!/usr/bin/python3
import re
import time
import pywikibot

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
for row in c.fetchall():
    r = row[0]
    print(r['county'])
    try:
        item_id = utils.get_qnumber(wikiarticle=r['electoral_area_title'], lang="zh-tw")
        if not item_id:
            raise
    except:
        labels = {"zh": r['electoral_area_title'], "zh-tw": r['electoral_area_title']}
        item_id = utils.create_item(wikidata_site, labels)
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    print(r['electoral_area_title'], item.id)

    # description & aliases
    if r['district'] and not item.descriptions.get('zh-tw'):
        descriptions = {'zh-tw': r['district'], 'zh': r['district']}
        item.editDescriptions(descriptions, asynchronous=False)
    if not item.aliases.get('zh-tw'):
        ref = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']
        aliases_label = re.sub('\d+', ref[r['constituency']-1], r['electoral_area_title'])
        print(aliases_label)
        aliases = {'zh-tw': [aliases_label], 'zh': [aliases_label]}
        item.editAliases(aliases, asynchronous=False)

    # electoral area

    # 性質
    try:
        if 'Q49924492' not in [x.target.id for x in item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
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
        item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        county_page = pywikibot.Page(site, r['county'])
        try:
            county_target = pywikibot.ItemPage.fromPage(county_page)
        except:
            county_q = utils.get_qnumber(wikiarticle=r['county'], lang="zh-tw")
            county_target = pywikibot.ItemPage(wikidata_site, county_q)
        claim.setTarget(county_target)
        item.addClaim(claim)
