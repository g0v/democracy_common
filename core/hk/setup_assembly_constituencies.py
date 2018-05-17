#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot

from common import utils


areas_ref = json.load(open('hk/data/national_areas.json'))
areas_ref = {x['itemLabel']: {
    'id': x['item'].split('/')[-1],
    'en': x['itemLabel_en'],
    'zh': x['itemLabel']
} for x in areas_ref if x.get('itemLabel')}

categories_ref = json.load(open('hk/data/national_categories.json'))
categories_ref = {x['itemLabel']: {
    'id': x['item'].split('/')[-1],
    'en': x['itemLabel_en'],
    'zh': x['itemLabel']
} for x in categories_ref if x.get('itemLabel')}

people = json.load(open('hk/data/assembly_people.json'))

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

counties, categories = set(), set()
for x in people:
    if x.get('county'):
        counties.add(x['county'])
    elif x.get('category'):
        categories.add(x['category'].replace('衞', '衛'))
print(len(counties), len(categories))
for county in counties:
    print(county, areas_ref.get(county))

for category in categories:
    ref = categories_ref.get(category)
    if not ref:
        ref = categories_ref.get('%s功能界別' % category)
    print(category, ref)

    item = pywikibot.ItemPage(repo, ref['id'])
    item.get()

    # labels &  description
    labels = {}
    for code in ['zh', 'zh-tw', 'zh-hant']:
        if category != item.labels.get(code):
            labels[code] = category
    item.editLabels(labels, asynchronous=False)
    descriptions = {'en': 'functional constituency of Hong Kong'}
    for code in ['zh', 'zh-tw', 'zh-hant']:
        if not item.descriptions.get(code):
            descriptions[code] = '香港立法會功能界別'
    item.editDescriptions(descriptions, asynchronous=False)

    # electoral area

    # 性質
    try:
        if 'Q5508804' not in [x.target.id for x in item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q5508804') # Q5508804 功能界別
        claim.setTarget(target)
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
        target = pywikibot.ItemPage(repo, 'Q8646') # Q8646 香港
        claim.setTarget(target)
        item.addClaim(claim)
