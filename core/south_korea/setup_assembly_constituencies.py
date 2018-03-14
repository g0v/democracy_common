#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot

from common import utils


people = json.load(open('south_korea/data/assembly_people.json'))

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

areas = set()
for x in people:
    if x['type'] == 'region':
        if x['county'] != x['constituency']:
            areas.add('%s %s' % (x['county'], x['constituency']))
        else:
            areas.add('%s' % x['county'])
print(len(areas))
for i, area in enumerate(areas):
    print(i, area)
    try:
        item_id = utils.get_qnumber(wikiarticle=area, lang="ko")
        if not item_id:
            raise
    except:
        labels = {"ko": area}
        item_id = utils.create_item(wikidata_site, labels)
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    print(area, item.id)

    # description
    if not item.descriptions.get('ko'):
        descriptions = {'ko': '%s 국회의원 선거구' % area} # 국회의원 선거구 國會議員選舉區
        item.editDescriptions(descriptions, asynchronous=False)

    # electoral area

    # 性質
    try:
        if 'Q50240982' not in [x.target.id for x in item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q50240982') # Q50240982 南韓國會議員選舉區
        claim.setTarget(target)
        item.addClaim(claim)

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
        item.claims['P131']
    except:
        claim = pywikibot.Claim(repo, 'P131')
        county_page = pywikibot.Page(site, area.split()[0])
        try:
            county_target = pywikibot.ItemPage.fromPage(county_page)
        except:
            county_q = utils.get_qnumber(wikiarticle=area.split()[0], lang="zh-tw")
            county_target = pywikibot.ItemPage(wikidata_site, county_q)
        claim.setTarget(county_target)
        item.addClaim(claim)
