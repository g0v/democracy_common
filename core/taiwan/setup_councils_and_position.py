#!/usr/bin/python3
import time
import pywikibot

from common import db_settings, utils


conn = db_settings.con_councilor()
c = conn.cursor()

overwrite = True

maps = {
    "基隆市": "http://www.kmc.gov.tw/",
    "臺北市": "http://www.tcc.gov.tw/",
    "新北市": "http://www.ntp.gov.tw/",
    "桃園市": "http://www.tycc.gov.tw/",
    "新竹市": "http://www.hsinchu-cc.gov.tw/",
    "新竹縣": "http://www.hcc.gov.tw/",
    "苗栗縣": "http://www.mcc.gov.tw/",
    "臺中市": "http://www.tccc.gov.tw/",
    "彰化縣": "http://www.chcc.gov.tw/",
    "南投縣": "http://www.ntcc.gov.tw/",
    "雲林縣": "http://www.ylcc.gov.tw/",
    "嘉義縣": "http://www.cyscc.gov.tw/",
    "嘉義市": "http://www.cycc.gov.tw/",
    "臺南市": "http://www.tncc.gov.tw/",
    "高雄市": "http://www.kcc.gov.tw/",
    "屏東縣": "http://www.ptcc.gov.tw/",
    "宜蘭縣": "http://www.ilcc.gov.tw/",
    "花蓮縣": "http://www.hlcc.gov.tw/",
    "臺東縣": "http://www.taitungcc.gov.tw/",
    "連江縣": "http://www.mtcc.gov.tw/",
    "金門縣": "http://www.kmcc.gov.tw/",
    "澎湖縣": "http://www.phcouncil.gov.tw/",
}

def create_item(site, label_dict):
    new_item = pywikibot.ItemPage(site)
    new_item.editLabels(labels=label_dict)
    return new_item.getID()

c.execute('''
    select row_to_json(_)
    from (
        select county, count(distinct(constituency)) as constituency_count, count(*) as seats
        from candidates_terms
        where election_year = '2014' and elected = true
        group by county
    ) _
''')

site = pywikibot.Site("zh", "wikipedia")
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
for row in c.fetchall():
    r = row[0]
    print(r['county'])
    council_name = '%s議會' % r['county']
    page = pywikibot.Page(site, council_name)
    item = pywikibot.ItemPage.fromPage(page)
    print(council_name, item.id)
    county_page = pywikibot.Page(site, r['county'])
    try:
        county_target = pywikibot.ItemPage.fromPage(county_page)
    except:
        county_q = utils.get_qnumber(wikiarticle=r['county'], lang="zh-tw")
        county_target = pywikibot.ItemPage(wikidata_site, county_q)

    # councilor position

    position = '%s議員' % r['county']
    try:
        match = False
        for q_id in utils.get_qnumber(wikiarticle=position, lang="zh-tw", limit=None):
            position_item = pywikibot.ItemPage(repo, q_id)
            position_item.get()
            if position_item.claims.get('P31') and 'Q4164871' in [x.target.id for x in position_item.claims['P31']]: # Q4164871 職位
                match = True
                break
        if not match:
            raise
    except:
        position_labels = {"zh": position, "zh-tw": position}
        position_item_id = create_item(wikidata_site, position_labels)
        position_item = pywikibot.ItemPage(repo, position_item_id)
        position_item.get()
        print('new position page created.')
    print(position, position_item.id)

    # 性質
    try:
        if 'Q4164871' not in [x.target.id for x in position_item.claims['P31']]:
            raise
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q4164871') # Q4164871 職位
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 上級分類
    try:
        position_item.claims['P279']
    except:
        claim = pywikibot.Claim(repo, 'P279')
        target = pywikibot.ItemPage(repo, 'Q708492') # Q708492 縣市議員
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 屬於
    try:
        position_item.claims['P361']
    except:
        claim = pywikibot.Claim(repo, 'P361')
        claim.setTarget(item)
        position_item.addClaim(claim)

    # 國家
    try:
        position_item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 中華民國
        claim.setTarget(target)
        position_item.addClaim(claim)

    # 管轄區域
    try:
        position_item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        claim.setTarget(county_target)
        position_item.addClaim(claim)

    # council

    if not item.labels.get('zh-tw'):
        labels = {'zh-tw': council_name}
        item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        if 'Q3308596' not in [x.target.id for x in item.claims['P31']]:
            raise
        if not overwrite:
            continue
    except:
        claim = pywikibot.Claim(repo, 'P31')
        target = pywikibot.ItemPage(repo, 'Q3308596') # Q3308596 市長－議會制
        claim.setTarget(target)
        item.addClaim(claim)

    # 國家
    try:
        item.claims['P17']
    except:
        claim = pywikibot.Claim(repo, 'P17')
        target = pywikibot.ItemPage(repo, 'Q865') # Q865 中華民國
        claim.setTarget(target)
        item.addClaim(claim)

    # 管轄區域
    try:
        item.claims['P1001']
    except:
        claim = pywikibot.Claim(repo, 'P1001')
        claim.setTarget(county_target)
        item.addClaim(claim)

    # 席次
    try:
        item.claims['P1342']
    except:
        claim = pywikibot.Claim(repo, 'P1342')
        target = pywikibot.WbQuantity(site=site, amount=r['seats'])
        claim.setTarget(target)
        item.addClaim(claim)

    # 選舉區數量
    try:
        item.claims['P4253']
    except:
        claim = pywikibot.Claim(repo, 'P4253')
        target = pywikibot.WbQuantity(site=site, amount=r['constituency_count'])
        claim.setTarget(target)
        item.addClaim(claim)

    # 子類
    try:
        item.claims['P527']
    except:
        claim = pywikibot.Claim(repo, 'P527')
        claim.setTarget(position_item)
        item.addClaim(claim)

    # 官方網站
    try:
        item.claims['P856']
    except:
        claim = pywikibot.Claim(repo, 'P856')
        claim.setTarget(maps[r['county']])
        item.addClaim(claim)
