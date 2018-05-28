#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot
from pywikibot import pagegenerators as pg

from common import utils


overwrite = True
people = json.load(open('hk/data/assembly_people.json'))
people.extend(json.load(open('hk/data/flacs_councilor.json')))
party_maps_path = 'hk/data/party_maps.json'
if os.path.isfile(party_maps_path):
    party_maps = json.load(open(party_maps_path))
else:
    party_maps = {}

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
parties = {x['party'].split('/')[0].strip() for x in people if x.get('party') and x['party'] != '無'}
for party in parties:
    print(party)
print(len(parties))
input('wait')
for party in parties:
    print(party)
    try:
        page = pywikibot.Page(site, party)
        item = pywikibot.ItemPage.fromPage(page)
        item.get()
        print(item)
        if [x.target.id for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']]:
            raise
        if 'Q7278' not in [x.target.id for x in item.claims['P31']]:
            continue
    except:
        match = False
        for item_id in utils.get_qnumber(wikiarticle=party, lang="zh", limit=None):
            print(item_id)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            try:
                if 'Q7278' in [x.target.id for x in item.claims['P31']]:
                    match = True
                    break
            except:
                continue
        if not match:
            print('no matched')
            continue
    print(item)
    if overwrite or not party_maps.get(party):
        party_maps[party] = item.id
json.dump(party_maps, open('hk/data/party_maps.json', 'w'), indent=2, ensure_ascii=False)
