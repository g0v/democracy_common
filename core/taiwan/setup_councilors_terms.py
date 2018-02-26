#!/usr/bin/python3
import re
import time
import pywikibot

from common import db_settings, utils


conn = db_settings.con_councilor()
c = conn.cursor()

overwrite = True
sleep_second = 5
ref = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']

c.execute('''
    select row_to_json(_)
    from (
        select county, election_year, min(term_start) as start_at,
            case
                when max(term_end->>'date')::date > now() then null
                else max(term_end->>'date')
            end as end_at
        from councilors_councilorsdetail
        where election_year > '2008'
        group by county, election_year
        order by county, election_year
    ) _
''')

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
for i, row in enumerate(c.fetchall()):
    r = row[0]
    print(i, r['county'])
    ad = utils.get_term_ad(r['county'], r['election_year'])
    term_name = '第%d屆%s議員' % (ad, r['county'])
    term_alias = '第%s屆%s議員' % (ref[ad-1], r['county'])
    term_description = '%s~%s%s議員' % (r['start_at'].split('-')[0], r['end_at'].split('-')[0] if r.get('end_at') else '', r['county']) if r.get('start_at') else None
    council_name = '%s議會' % r['county']

    try:
        item_id = utils.get_qnumber(wikiarticle=term_name, lang="zh-tw")
        if not item_id:
            raise
        else:
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
            if item.labels['zh'] != term_name:
                raise
    except:
        labels = {"zh": term_name, "zh-tw": term_name, "zh-hant": term_name}
        item_id = utils.create_item(wikidata_site, labels)
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    print(term_name, item.id)

    # aliases
    if term_description and not item.descriptions.get('zh-hant'):
        descriptions = {'zh-hant': term_description, 'zh-tw': term_description, 'zh': term_description}
        item.editDescriptions(descriptions, asynchronous=False)
    if not item.aliases.get('zh-tw'):
        aliases = {'zh-hant': [term_alias], 'zh-tw': [term_alias], 'zh': [term_alias]}
        item.editAliases(aliases, asynchronous=False)

    # terms

    # 性質
    try:
        item.claims['P31']
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q15238777') # Q15238777 legislative term
        claim.setTarget(target)
        item.addClaim(claim)
    claim = item.claims['P31'][0]

    # 關於
    try:
        qualifier = claim.qualifiers['P642']
    except:
        qualifier = pywikibot.Claim(repo, 'P642')
        page = pywikibot.Page(site, council_name)
        try:
            target = pywikibot.ItemPage.fromPage(page)
        except:
            target_q = utils.get_qnumber(wikiarticle=council_name, lang="zh-tw")
            target = pywikibot.ItemPage(wikidata_site, target_q)
        qualifier.setTarget(target)
        claim.addQualifier(qualifier)
        time.sleep(sleep_second)

    # 系列序號
    try:
        qualifier = claim.qualifiers['P1545']
    except:
        qualifier = pywikibot.Claim(repo, 'P1545')
        qualifier.setTarget(str(ad))
        claim.addQualifier(qualifier)

    # start_at
    if r.get('start_at'):
        try:
            item.claims['P571']
        except:
            claim = pywikibot.Claim(repo, 'P571')
            year, month, day = [int(x) for x in r['start_at'].split('-')]
            target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
            claim.setTarget(target)
            item.addClaim(claim)

    # end_at
    if r.get('end_at'):
        try:
            item.claims['P576']
        except:
            claim = pywikibot.Claim(repo, 'P576')
            year, month, day = [int(x) for x in r['end_at'].split('-')]
            target = pywikibot.WbTime(year=year, month=month, day=day, precision='day')
            claim.setTarget(target)
            item.addClaim(claim)
