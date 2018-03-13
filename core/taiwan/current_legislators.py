#!/usr/bin/python3
import json
import time
import pywikibot

from common import db_settings, utils


conn = db_settings.con_ly()
c = conn.cursor()

sleep_second = 5
site = pywikibot.Site("zh", "wikipedia")
repo = site.data_repository()
ad = 9
election_years = [1989, 1992, 1995, 1998, 2001, 2004, 2008, 2012, 2016, 2020]
election_title = '%d年立法委員選舉' % election_years[ad-1]
election_id = utils.get_qnumber(wikiarticle=election_title, lang="zh-tw")
election_target = pywikibot.ItemPage(repo, election_id)
term_id = utils.get_qnumber(wikiarticle="第%d屆立法委員" % ad, lang="zh-tw")
term_target = pywikibot.ItemPage(repo, term_id)

def person_qid_from_db(name):
    c.execute('''
        select lm.data->>'wikidata_qid'
        from legislator_legislatordetail l
        left join legislator_legislator lm on l.legislator_id = lm.uid
        where l.ad = %s and l.name = %s
    ''', [ad, name])
    r = c.fetchone()
    if r:
        return r[0]

def person_from_db(name):
    c.execute('''
        select row_to_json(_)
        from (
            select l.*, c.district, c.gender, lm.identifiers, cm.birth, jsonb_array_length(identifiers) as names_count
            from legislator_legislatordetail l
            left join candidates_terms c on c.legislator_id = l.id
            left join candidates_candidates cm on c.candidate_id = cm.uid
            left join legislator_legislator lm on l.legislator_id = lm.uid
            where l.ad = %s and l.name = %s
        ) _
    ''', [ad, name])
    return c.fetchone()[0]

c.execute('''
    select row_to_json(_)
    from (
        select l.*, c.district, c.gender, lm.identifiers, cm.birth, lm.data->>'wikidata_qid' as wikidata_qid, jsonb_array_length(identifiers) as names_count
        from legislator_legislatordetail l
        left join candidates_terms c on c.legislator_id = l.id
        left join candidates_candidates cm on c.candidate_id = cm.uid
        left join legislator_legislator lm on l.legislator_id = lm.uid
        where l.ad = %s
    ) _
''', [ad, ])
for i, r in enumerate(c.fetchall()):
    person = r[0]
    item = utils.person_page_item(person)
    item.get()
    print(i, person['name'], item.id)

    # Labels & Aliase
    if not item.labels.get('zh-hant'):
        labels = {'zh-hant': person['name'], 'zh-tw': person['name'], 'zh': person['name']}
        item.editLabels(labels, asynchronous=False)
    if person['names_count'] > 1 and not item.aliases.get('zh-tw'):
        aliases = {'zh-hant': person['identifiers'], 'zh-tw': person['identifiers'], 'zh': person['identifiers']}
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
            target = pywikibot.ItemPage(repo, utils.gender_id(person['gender']))
            claim.setTarget(target)
            item.addClaim(claim)

    # 生日
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

    # term_start
    term_start_year, term_start_month, term_start_day = [int(x) for x in person['term_start'].split('-')]
    term_start_target = pywikibot.WbTime(year=term_start_year, month=term_start_month, day=term_start_day, precision='day')
    # Q6310593 立法委員
    try:
        match = False
        for i, x in enumerate(item.claims['P39']):
            if x.target.id == 'Q6310593':
                if len(x.qualifiers) == 0 or term_start_target == x.qualifiers['P580'][0].target:
                    claim = item.claims['P39'][i]
                    match = True
                    break
        if not match:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P39')
        target = pywikibot.ItemPage(repo, 'Q6310593')
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
        qualifier.setTarget(election_target)
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
                    if x.target.id == 'Q6310593':
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
    try:
        qualifier = claim.qualifiers['P4100']
    except:
        qualifier = pywikibot.Claim(repo, 'P4100')
        party = utils.get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
        target = pywikibot.ItemPage(repo, party)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # terms
    try:
        qualifier = claim.qualifiers['P2937']
    except:
        qualifier = pywikibot.Claim(repo, 'P2937')
        qualifier.setTarget(term_target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # constituency
    if person['county'] in ['全國不分區', '僑居國外國民']:
        constituency_label = '全國不分區'
        constituency = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
    elif person['county'] in ['平地原住民', '山地原住民']:
        constituency_label = '%s立法委員選區' % person['county']
        constituency = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
    else:
        constituency_label = "%s第%s選舉區" % (person['county'], utils.zh_number(person['constituency']))
        constituency = utils.get_qnumber(wikiarticle=constituency_label, lang="zh-tw")
        if not constituency and person['county'] == '桃園市':
            constituency = utils.get_qnumber(wikiarticle="桃園縣第%s選舉區" % (utils.zh_number(person['constituency'])), lang="zh-tw")
        elif not constituency and person['constituency'] == 1:
            constituency_label = "%s選舉區" % (person['county'])
            constituency = utils.get_qnumber(constituency_label, lang="zh-tw")
    try:
        claim.qualifiers['P768']
    except:
        print(constituency_label, constituency)
        qualifier = pywikibot.Claim(repo, 'P768')
        target = pywikibot.ItemPage(repo, constituency)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    c.execute('''
        UPDATE legislator_legislator
        SET data = (COALESCE(data, '{}'::jsonb) || %s::jsonb)
        WHERE uid = %s
    ''', (json.dumps({
        'wikidata_qid': item.id,
        'wikidata': item.toJSON()
    }), person['legislator_id']))
    conn.commit()
