#!/usr/bin/python3
import os
import json
import time
import pywikibot
from pywikibot import pagegenerators as pg
import logging

from common import db_settings, utils


logging.basicConfig(filename='parser.log', level=logging.CRITICAL)

conn = db_settings.con_councilor()
c = conn.cursor()

overwrite = True
sleep_second = 5
election_year = '2014'
election_ids = {
    '2014': 'Q15902729'
}
election_id = election_ids[election_year]

def person_qid_from_db(name):
    c.execute('''
        select lm.data->>'wikidata_qid'
        from councilors_councilorsdetail l
        left join councilors_councilors lm on l.councilor_id = lm.uid
        where l.election_year = %s and (l.name = %s or lm.identifiers ? %s)
    ''', [election_year, name, name])
    r = c.fetchone()
    if r:
        return r[0]

def person_from_db(name):
    c.execute('''
        select row_to_json(_)
        from (
            select l.*, c.district, c.gender, lm.identifiers, cm.birth, jsonb_array_length(cm.identifiers) as names_count
            from councilors_councilorsdetail l
            left join candidates_terms c on c.elected_councilor_id = l.id
            left join candidates_candidates cm on c.candidate_id = cm.uid
            left join councilors_councilors lm on l.councilor_id = lm.uid
            where l.election_year = %s and (l.name = %s or lm.identifiers ? %s)
        ) _
    ''', [election_year, name, name])
    return c.fetchone()[0]

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
wikidata_repo = wikidata_site.data_repository()
position_maps_path = 'taiwan/data/councilor_position_maps.json'
if os.path.isfile(position_maps_path):
    position_maps = json.load(open(position_maps_path))
else:
    query = '''
        SELECT ?item ?itemLabel WHERE {
            ?item wdt:P31 wd:Q4164871; # Q4164871 職位
                wdt:P17 wd:Q865; # Q865 中華民國
                wdt:P279 wd:Q708492.
            SERVICE wikibase:label { bd:serviceParam wikibase:language "zh-tw". }
        }
    '''
    generator = pg.WikidataSPARQLPageGenerator(query, site=wikidata_site)
    position_maps = {page.get()['labels']['zh-tw']: page.id for page in generator}
    json.dump(position_maps, open('taiwan/data/councilor_position_maps.json', 'w'), indent=2, ensure_ascii=False)
c.execute('''
    select row_to_json(_)
    from (
        select l.*, c.constituency, coalesce(c.district, l.district) as district, coalesce(c.gender, l.gender) as gender, lm.identifiers, coalesce(lm.birth, cm.birth) as birth, lm.data->>'wikidata_qid' as wikidata_qid, coalesce(jsonb_array_length(cm.identifiers), 0) as names_count, l.county || '議員第' || c.constituency || '選舉區' as electoral_area_title
        from councilors_councilorsdetail l
        left join candidates_terms c on c.elected_councilor_id = l.id
        left join candidates_candidates cm on c.candidate_id = cm.uid
        left join councilors_councilors lm on l.councilor_id = lm.uid
        where l.election_year = %s
        order by l.county, l.constituency
    ) _
''', [election_year, ])
for i, r in enumerate(c.fetchall()):
    person = r[0]
    print(i, person['name'])
    item = utils.person_page_item(person)
    print(item.id)

    # Labels & Aliase
    if not item.labels.get('zh-hant'):
        labels = {'zh-hant': person['name'], 'zh-tw': person['name']}
        item.editLabels(labels, asynchronous=False)
    if person['names_count'] > 1 and not item.aliases.get('zh-tw'):
        aliases = {'zh-tw': person['identifiers'], 'zh': person['identifiers']}
        item.editAliases(aliases, asynchronous=False)

    # 性質
    try:
        item.claims['P31']
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q5')
        claim.setTarget(target)
        item.addClaim(claim)

    # Q82955 政治人物
    try:
        if 'Q82955' not in [x.target.id for x in item.claims['P106']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P106')
        target = pywikibot.ItemPage(repo, 'Q82955')
        claim.setTarget(target)
        item.addClaim(claim)

    # 性別
    if person['gender']:
        try:
            item.claims['P21']
        except:
            claim = pywikibot.Claim(repo, 'P21')
            target = pywikibot.ItemPage(repo, utils.gender_id[person['gender']])
            claim.setTarget(target)
            item.addClaim(claim)

    # 生日
    # most councilors didn't have birth date but only birth year at this time 2018-02-25
    if person['birth']:
        try:
            item.claims['P569']
        except:
            claim = pywikibot.Claim(repo, 'P569')
            b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
            if b_month == 1 and b_day == 1:
                b_year_target = pywikibot.WbTime(year=b_year, precision='year')
                claim.setTarget(b_year_target)
            else:
                b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
                claim.setTarget(b_target)
            item.addClaim(claim)

    # term
    ad = utils.get_term_ad(person['county'], person['election_year'])
    term_name = '第%d屆%s議員' % (ad, person['county'])
    term_id = utils.get_qnumber(wikiarticle=term_name, lang="zh-tw")
    term_target = pywikibot.ItemPage(repo, term_id)
    # term_start
    term_start_year, term_start_month, term_start_day = [int(x) for x in person['term_start'].split('-')]
    term_start_target = pywikibot.WbTime(year=term_start_year, month=term_start_month, day=term_start_day, precision='day')
    # XX縣市議員
    position_held_id = position_maps['%s議員' % person['county']]
    try:
        match = False
        for i, x in enumerate(item.claims['P39']):
            if x.target.id == position_held_id:
                if len(x.qualifiers) == 0 or term_start_target == x.qualifiers['P580'][0].target:
                    claim = item.claims['P39'][i]
                    match = True
                    break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P39')
        target = pywikibot.ItemPage(repo, position_held_id)
        claim.setTarget(target)
        item.addClaim(claim)

    # start at
    try:
        qualifier = claim.qualifiers['P580']
    except:
        qualifier = pywikibot.Claim(repo, 'P580')
        qualifier.setTarget(term_start_target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # 選舉於
    try:
        qualifier = claim.qualifiers['P2715']
    except:
        qualifier = pywikibot.Claim(repo, 'P2715')
        target = pywikibot.ItemPage(repo, election_id)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

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
            time.sleep(sleep_second)
        # replaced by
        if person['term_end'].get('replacement'):
            print('replaced by: "%s"' % person['term_end']['replacement'])
            target_id = person_qid_from_db(person['term_end']['replacement'])
            if target_id:
                target = pywikibot.ItemPage(repo, target_id)
            else:
                target = utils.person_page_item(person_from_db(person['term_end']['replacement']))
            try:
                claim.qualifiers['P1366']
            except:
                qualifier = pywikibot.Claim(repo, 'P1366')
                qualifier.setTarget(target)
                claim.addQualifier(qualifier)
                time.sleep(sleep_second)
            # replaces
            try:
                match = False
                for i, x in enumerate(target.claims['P39']):
                    if x.target.id == position_held_id:
                        if term_id == x.qualifiers['P2937'][0].target.id:
                            claim = item.claims['P39'][i]
                            match = True
                            break
                if match:
                    try:
                        claim.qualifiers['P1365']
                    except:
                        qualifier = pywikibot.Claim(repo, 'P1365')
                        qualifier.setTarget(item)
                        claim.addQualifier(qualifier)
                        time.sleep(sleep_second)
            except:
                pass

    # party
    if person['party'] and person['party'] != '無黨籍':
        try:
            qualifier = claim.qualifiers['P4100']
        except:
            qualifier = pywikibot.Claim(repo, 'P4100')
            party = utils.get_qnumber(wikiarticle=person['party'], lang="zh-tw")
            target = pywikibot.ItemPage(repo, party)
            qualifier.setTarget(target)
            claim.addQualifier(qualifier)
            time.sleep(sleep_second)

    # terms
    try:
        qualifier = claim.qualifiers['P2937']
#       if qualifier[0].target != term_target:
#           claim.removeQualifiers(qualifier)
#           raise
    except:
        qualifier = pywikibot.Claim(repo, 'P2937')
        qualifier.setTarget(term_target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # constituency
    try:
        qualifier = claim.qualifiers['P768']
    except:
        qualifier = pywikibot.Claim(repo, 'P768')
        item_id = utils.get_qnumber(wikiarticle=person['electoral_area_title'], lang="zh-tw")
        target = pywikibot.ItemPage(repo, item_id)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    c.execute('''
        UPDATE councilors_councilors
        SET data = (COALESCE(data, '{}'::jsonb) || %s::jsonb)
        WHERE uid = %s
    ''', (json.dumps({
        'wikidata_qid': item.id,
        'wikidata': item.toJSON()
    }), person['councilor_id']))
    conn.commit()
