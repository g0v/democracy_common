#!/usr/bin/python3
import os
import re
import json
import time
import pywikibot
from pywikibot import pagegenerators as pg

from common import utils


overwrite = True
people = json.load(open('south_korea/data/assembly_people.json'))
people.extend(json.load(open('south_korea/data/flacs_councilor.json')))
party_maps_path = 'south_korea/data/party_maps.json'
if os.path.isfile(party_maps_path):
    party_maps = json.load(open(party_maps_path))
else:
    party_maps = {}

site = pywikibot.Site("ko", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
parties = {x['party'] for x in people}
print(len(parties))
for party in parties:
    print(party)
    if party == '무소속': # 無黨籍 무소속
        party_maps[party] = None
        continue
    try:
        page = pywikibot.Page(site, party)
        item = pywikibot.ItemPage.fromPage(page)
        item.get()
        print(item)
        if 'Q884' not in [x.target.id for x in item.claims['P17']] or [x.target.id for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']]:
            raise
    except:
        match = False
        for item_id in utils.get_qnumber(wikiarticle=party, lang="ko", limit=None):
            print(item_id)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            try:
                if 'Q7278' in [x.target.id for x in item.claims['P31']] and 'Q884' in [x.target.id for x in item.claims['P17']]:
                    match = True
                    break
            except:
                continue
        if not match:
            raise
    print(item)
    if overwrite or not party_maps.get(party):
        party_maps[party] = item.id
json.dump(party_maps, open('south_korea/data/party_maps.json', 'w'), indent=2, ensure_ascii=False)
