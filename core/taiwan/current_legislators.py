#!/usr/bin/python3
import time
from datetime import datetime
from requests import get
import pywikibot

from common import db_settings


def get_qnumber(wikiarticle, lang, limit=1):
    params={
        'action': 'wbsearchentities',
        'search': wikiarticle,
        'language': lang,
        'uselang': lang,
        'format': 'json',
        'type': 'item'
    }
    if limit:
        params['limit'] = limit
    resp = get('https://www.wikidata.org/w/api.php', params=params).json()
    if resp.get('search') and limit:
        return resp['search'][0]['id']
    else:
        return [x['id'] for x in resp['search']]

conn = db_settings.con_ly()
c = conn.cursor()

overwrite = True

c.execute('''
    select row_to_json(_)
    from (
        select l.*, c.district, c.gender, lm.identifiers, cm.birth
        from legislator_legislatordetail l
        left join candidates_terms c on c.legislator_id = l.id
        left join candidates_candidates cm on c.candidate_id = cm.uid
        left join legislator_legislator lm on l.legislator_id = lm.uid
        where l.ad = 9 and l.name = '趙天麟'
    ) _
''')
for r in c.fetchall()[:]:
    person = r[0]
    site = pywikibot.Site("zh", "wikipedia")
    repo = site.data_repository()
    for name in person['identifiers']:
        print(name)
        try:
            page = pywikibot.Page(site, name)
            item = pywikibot.ItemPage.fromPage(page)
            break
        except:
            site = pywikibot.Site("wikidata", "wikidata")
            repo = site.data_repository()
            name_q = get_qnumber(wikiarticle=name, lang="zh-tw")
            item = pywikibot.ItemPage(site, name_q)
            try:
                item.get()
            except pywikibot.exceptions.NoPage:
                continue
            labels = {'zh-tw': name, 'zh': name}
            item.editLabels(labels, asynchronous=False)
            break
    # Q4167410 維基媒體消歧義頁
    if item.claims['P31'][0].target.id == 'Q4167410':
        try:
            item.removeClaims(item.claims['P39'][0])
        except:
            pass
        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()
        party = get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
        b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
        b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
        for q_id in get_qnumber(wikiarticle=person['name'], lang="zh-tw", limit=None):
            item = pywikibot.ItemPage(site, q_id)
            item.get()
            if item.claims.get('P569') and item.claims['P569'][0].target == b_target:
                break
            if item.claims.get('P102') and item.claims['P102'][0].target.id == party:
                break
    print(item)

    # Q6310593 立法委員
    try:
        item.claims['P39']
        if not overwrite:
            continue
    except:
        claim = pywikibot.Claim(repo, 'P39')
        target = pywikibot.ItemPage(repo, "Q6310593")
        claim.setTarget(target)
        item.addClaim(claim)
    finally:
        claim = item.claims['P39'][0]

    # start at
    try:
        qualifier = claim.qualifiers['P580']
    except:
        qualifier = pywikibot.Claim(repo, 'P580')
        year, month, day = [int(x) for x in person['term_start'].split('-')]
        target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(10)

    if person['in_office'] == False and person['term_end']:
        # end at
        try:
            qualifier = claim.qualifiers['P582']
        except:
            qualifier = pywikibot.Claim(repo, 'P582')
            year, month, day = [int(x) for x in person['term_end']['date'].split('-')]
            target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
            qualifier.setTarget(target)
            claim.addQualifier(qualifier)
            time.sleep(10)

    # party
    try:
        qualifier = claim.qualifiers['P4100']
    except:
        qualifier = pywikibot.Claim(repo, 'P4100')
        party = get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
        target = pywikibot.ItemPage(repo, party)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(10)

    # terms
    try:
        qualifier = claim.qualifiers['P2937']
    except:
        qualifier = pywikibot.Claim(repo, 'P2937')
        term = get_qnumber(wikiarticle="第%d屆立法委員" % person['ad'], lang="zh-tw")
        target = pywikibot.ItemPage(repo, term)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(10)

    # constituency
    if person['county'] == '全國不分區':
        constituency_label = person['county']
        aliase = constituency_label
        constituency = get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
    else:
        ref = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']
        constituency_label = "%s第%s選舉區" % (person['county'], ref[person['constituency']-1])
        aliase = "%s第%d選舉區" % (person['county'], person['constituency'])
        constituency = get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
        if not constituency and person['county'] == '桃園市':
            constituency = get_qnumber(wikiarticle="桃園縣第%s選舉區" % (ref[person['constituency']-1]), lang="zh-tw")
        elif not constituency and person['constituency'] == 1:
            constituency_label = "%s選舉區" % (person['county'])
            aliase = constituency_label
            constituency = get_qnumber(constituency_label, lang="zh-tw")
    try:
        qualifier = claim.qualifiers['P768']
    except:
        print(constituency_label, constituency, aliase)
        qualifier = pywikibot.Claim(repo, 'P768')
        target = pywikibot.ItemPage(repo, constituency)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(10)

#   time.sleep(3)
    if person['county'] != '全國不分區':
        wikidata_site = pywikibot.Site("wikidata", "wikidata")
        repo = wikidata_site.data_repository()
        c_item = pywikibot.ItemPage(wikidata_site, constituency)
        labels = {'zh-tw': constituency_label}
        print(labels)
        c_item.editLabels(labels, asynchronous=False)
        if aliase != constituency_label:
            aliases = {'zh-tw': [aliase], 'zh': [aliase]}
            c_item.editAliases(aliases, asynchronous=False)
        if person['district']:
            descriptions = {'zh-tw': person['district'], 'zh': person['district']}
            c_item.editDescriptions(descriptions, asynchronous=False)
