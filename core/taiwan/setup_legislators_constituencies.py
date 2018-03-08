#!/usr/bin/python3
import os
import re
import json
import time
from collections import defaultdict
import pywikibot

from common import db_settings, utils


conn = db_settings.con_ly()
c = conn.cursor()

ad = 9

c.execute('''
    select row_to_json(_)
    from (
        select l.county, c.constituency, c.district
        from legislator_legislatordetail l
        left join candidates_terms c on c.legislator_id = l.id
        where l.ad = %s
        group by l.county, c.constituency, c.district
        order by l.county, c.constituency
    ) _
''', [ad, ])

wiki_maps_path = 'taiwan/data/city_councils_councilor_maps.json'
wiki_maps = json.load(open(wiki_maps_path))

site = pywikibot.Site("zh", "wikipedia")
repo = site.data_repository()
wikidata_site = pywikibot.Site("wikidata", "wikidata")
wikidata_repo = wikidata_site.data_repository()
for r in c.fetchall():
    r = r[0]
    print(r['county'], r['constituency'], )

    # constituency
    if r['county'] == '全國不分區':
        constituency_label = r['county']
        constituency_id = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
        print(constituency_id)
    elif r['county'] in ['平地原住民', '山地原住民']:
        constituency_label = '%s立法委員選區' % r['county']
        constituency_id = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
        item = pywikibot.ItemPage(wikidata_site, constituency_id)
        item.get()

        # 國家
        try:
            item.claims['P17']
        except:
            claim = pywikibot.Claim(repo, 'P17')
            target = pywikibot.ItemPage(repo, 'Q865') # Q865 Taiwan
            claim.setTarget(target)
            item.addClaim(claim)

        # Right to vote
        try:
            item.claims['P2964']
        except:
            claim = pywikibot.Claim(repo, 'P2964')
            target = pywikibot.ItemPage(repo, utils.aborigine_id(r['constituency_type_title']))
            claim.setTarget(target)
            item.addClaim(claim)
    else:
        constituency_label = "%s第%s選舉區" % (r['county'], utils.zh_number(r['constituency']))
        data = defaultdict(dict)
        aliases_label = []
        for x in [utils.zh_number(r['constituency']), '%d' % r['constituency'], '%02d' % r['constituency']]:
            for y in ['選舉區', '選區']:
                if re.search('^[臺台]', r['county']):
                    for z in [re.sub('^臺', '台', r['county']), re.sub('^台', '臺', r['county'])]:
                        aliases_label.append("%s第%s%s" % (z, x, y))
                else:
                    aliases_label.append("%s第%s%s" % (r['county'], x, y))
        constituency_id = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
        if not constituency_id and r['constituency'] == 1:
            constituency_label = "%s選舉區" % (r['county'])
            aliases_label.extend([
                constituency_label,
                "%s選區" % (r['county']),
            ])
            constituency_id = utils.get_qnumber(constituency_label, lang="zh-tw")
        print(constituency_label, constituency_id)

        for f in wiki_maps:
            if f['cityLabel'] == r['county']:
                r['city'] = f['city'].split('/')[-1]
                r['cityLabel_en'] = f['cityLabel_en']
                break

        item = pywikibot.ItemPage(wikidata_site, constituency_id)
        item.get()

        # English Labels
        if not item.labels.get('en'):
            labels = {'en': '%s Constituency of National Legislators of %s' % (utils.ordinal_number(r['constituency']), r['cityLabel_en'])}
            item.editLabels(labels, asynchronous=False)

        # labels, descriptions, aliases
        labels, descriptions = constituency_label, r['district']
        for code in ['zh', 'zh-tw', 'zh-hant']:
            if item.labels.get(code, '') != labels:
                data['labels'][code] = labels
            if item.descriptions.get(code, '') != descriptions:
                data['descriptions'][code] = descriptions
        if bool(data):
            item.editEntity(data, asynchronous=False)
        for code in ['zh', 'zh-tw', 'zh-hant']:
            aliases_exist = item.aliases.get(code, [])
            aliases_not_exist = [alias for alias in aliases_label if alias not in aliases_exist]
            data['aliases'][code] = aliases_exist + aliases_not_exist
        item.editEntity(data, asynchronous=False)

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
