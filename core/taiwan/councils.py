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
    # Add description here or in another function
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
repo = site.data_repository()
for row in c.fetchall()[18:]:
    r = row[0]
    council_name = '%s議會' % r['county']
    page = pywikibot.Page(site, council_name)
    item = pywikibot.ItemPage.fromPage(page)
    print(r['county'], item.id)

    if not item.labels.get('zh-tw'):
        labels = {'zh-tw': council_name}
        item.editLabels(labels, asynchronous=False)

    # 性質
    try:
        if 'Q3308596' not in [x.target.id for x in item.claims['P31']]:
            raise
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
        county_page = pywikibot.Page(site, r['county'])
        try:
            target = pywikibot.ItemPage.fromPage(county_page)
        except:
            wikidata_site = pywikibot.Site("wikidata", "wikidata")
            county_q = get_qnumber(wikiarticle=r['county'], lang="zh-tw")
            target = pywikibot.ItemPage(wikidata_site, county_q)
        claim = pywikibot.Claim(repo, 'P1001')
        claim.setTarget(target)
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

    # 官方網站
    try:
        item.claims['P856']
    except:
        claim = pywikibot.Claim(repo, 'P856')
        claim.setTarget(maps[r['county']])
        item.addClaim(claim)

#   some_labels = {"zh": "新北市議員", "zh-tw": "新北市議員"}
#   new_item_id = create_item(site, some_labels)
#   print(new_item_id)
