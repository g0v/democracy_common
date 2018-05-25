#!/usr/bin/python3
import os
import re
import json
import time
import codecs
import requests
import pywikibot

from common import utils


people_path = 'south_korea/data/flacs_councilor.json'
people = json.load(open(people_path))
people = {x['name'] for x in people if x.get('wikidata_qid')}
for l in ['municipal_member.json', 'province_member.json'][1:]:
    sns_path = 'south_korea/data/sns/%s' % l
    if not os.path.isfile(sns_path):
        url = 'https://raw.githubusercontent.com/teampopong/data-election/master/local/2014-06-04/sns/links_%s' % l
        r = requests.get(url).json()

        with codecs.open(sns_path, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        r = json.load(open(sns_path))
    print(l, len(r))
    sns_names = {x['name'] for x in r if x['links'].get('facebook')}

    for person in sns_names.intersection(people):
        print(person)

#site = pywikibot.Site("ko", "wikipedia")
#wikidata_site = pywikibot.Site("wikidata", "wikidata")
#repo = site.data_repository()
