#!/usr/bin/python3
import requests
import pywikibot


def gender_id(text):
    return {
        '男': 'Q6581097',
        '남': 'Q6581097',
        '女': 'Q6581072',
        '여': 'Q6581072'
    }[text]

def aborigine_id(text):
    return {
        '平地原住民': 'Q50355511',
        '山地原住民': 'Q50355510'
    }[text]


def zh_number(number):
    return ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九'][number-1]

def ordinal_number(number):
    return ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th',
'12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st',
'22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st'][number-1]

def get_term_ad(county, election_year):
    return {
        "臺北市": {'1969': 1, '1973': 2, '1977': 3, '1981': 4, '1985': 5, '1989': 6, '1994': 7, '1998': 8, '2002': 9, '2006': 10, '2010': 11, '2014': 12, '2018': 13},
        "新北市": {'2010': 1, '2014': 2, '2018': 3},
        "臺北縣": {'1951': 1, '1953': 2, '1955': 3, '1958': 4, '1961': 5, '1964': 6, '1968': 7, '1973': 8, '1977': 9, '1982': 10, '1986': 11, '1990': 12, '1994': 13, '1998': 14, '2002': 15, '2006': 16},
        "高雄市": {'2010': 1, '2014': 2, '2018': 3},
        "臺南市": {'2010': 1, '2014': 2, '2018': 3},
        "臺中市": {'2010': 1, '2014': 2, '2018': 3},
        "桃園市": {'2014': 1, '2018': 19},
        "桃園縣": {'2009': 17},
        "南投縣": {'2009': 17, '2014': 18, '2018': 19},
        "宜蘭縣": {'2009': 17, '2014': 18, '2018': 19},
        "澎湖縣": {'2009': 17, '2014': 18, '2018': 19},
        "屏東縣": {'2009': 17, '2014': 18, '2018': 19},
        "新竹市": {'2009': 8, '2014': 9, '2018': 10},
        "新竹縣": {'2009': 17, '2014': 18, '2018': 19},
        "雲林縣": {'2009': 17, '2014': 18, '2018': 19},
        "基隆市": {'2009': 17, '2014': 18, '2018': 19},
        "嘉義縣": {'2009': 17, '2014': 18, '2018': 19},
        "彰化縣": {'2009': 17, '2014': 18, '2018': 19},
        "臺東縣": {'2009': 17, '2014': 18, '2018': 19},
        "花蓮縣": {'2009': 17, '2014': 18, '2018': 19},
        "嘉義市": {'2009': 17, '2014': 18, '2018': 19},
        "苗栗縣": {'2009': 17, '2014': 18, '2018': 19},
        "連江縣": {'2009': 5, '2014': 6, '2018': 7},
        "金門縣": {'2009': 5, '2014': 6, '2018': 7}
    }[county].get(election_year)


def get_korea_flacs_councilor_term_ad(county, election_year, get_end_year=False):
    maps = {
        "서울특별시": {'1991': 3, '1995': 4, '1998': 5, '2002': 6, '2006': 7, '2010': 8, '2014': 9, '2018': 10},
        "부산광역시": {'1991': 1, '1995': 2, '1998': 3, '2002': 4, '2006': 5, '2010': 6, '2014': 7, '2018': 8},
        "대구광역시": {'1991': 1, '1995': 2, '1998': 3, '2002': 4, '2006': 5, '2010': 6, '2014': 7, '2018': 8},
        "인천광역시": {'1991': 1, '1995': 2, '1998': 3, '2002': 4, '2006': 5, '2010': 6, '2014': 7, '2018': 8},
        "광주광역시": {'1991': 1, '1995': 2, '1998': 3, '2002': 4, '2006': 5, '2010': 6, '2014': 7, '2018': 8},
        "대전광역시": {'1991': 1, '1995': 2, '1998': 3, '2002': 4, '2006': 5, '2010': 6, '2014': 7, '2018': 8},
        "울산광역시": {'1995': 1, '1998': 2, '2002': 3, '2006': 4, '2010': 5, '2014': 6, '2018': 7},
        "세종특별자치시": {'2012': 1, '2014': 2, '2018': 3},
        "경기도": {'1991': 3, '1995': 4, '1998': 5, '2002': 6, '2006': 7, '2010': 8, '2014': 9, '2018': 10},
        "강원도": {'1991': 3, '1995': 4, '1998': 5, '2002': 6, '2006': 7, '2010': 8, '2014': 9, '2018': 10},
        "충청북도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "충청남도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "전라북도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "전라남도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "경상북도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "경상남도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
        "제주특별자치도": {'1991': 4, '1995': 5, '1998': 6, '2002': 7, '2006': 8, '2010': 9, '2014': 10, '2018': 11},
    }
    if not get_end_year:
        return maps[county].get(election_year)
    else:
        current_ad =  maps[county].get(election_year)
        for year, ad in maps[county].items():
            if ad == (current_ad + 1):
                return year
        return ''

def get_qnumber(wikiarticle, lang, limit=1):
    params = {
        'action': 'wbsearchentities',
        'search': wikiarticle,
        'language': lang,
        'uselang': lang,
        'format': 'json',
        'type': 'item'
    }
    if limit:
        params['limit'] = limit
    resp = requests.get('https://www.wikidata.org/w/api.php', params=params).json()
    if resp.get('search') and limit:
        return resp['search'][0]['id']
    else:
        r = resp['search']
        if resp.get('search-continue'):
            params['continue'] = resp['search-continue']
            resp_c = requests.get('https://www.wikidata.org/w/api.php', params=params).json()
            r.extend(resp_c['search'])
        return [x['id'] for x in r]

def create_item(site, label_dict):
    new_item = pywikibot.ItemPage(site)
    new_item.editLabels(labels=label_dict)
    return new_item.getID()

def person_page_item(person):
    site = pywikibot.Site("zh", "wikipedia")
    wikidata_site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    wikidata_repo = wikidata_site.data_repository()
    if person.get('wikidata_qid'):
        item = pywikibot.ItemPage(repo, person['wikidata_qid'])
        item.get()
        return item
    for name in person['identifiers']:
        print(name)
        try:
            page = pywikibot.Page(site, name)
            item = pywikibot.ItemPage.fromPage(page)
            break
        except:
            name_q = get_qnumber(wikiarticle=name, lang="zh-tw")
            try:
                item = pywikibot.ItemPage(wikidata_site, name_q)
            except:
                continue
            break

    try:
        item.get()
        if person.get('birth'):
            b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
            b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
            match = True
            # Q4167410 維基媒體消歧義頁, Q13406463 維基媒體列表條目
            if [x for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']] or (item.claims.get('P569') and b_target not in [x.target for x in item.claims['P569']]) or (item.claims.get('P569') and b_month == 1 and b_day == 1 and b_year not in [x.target.year for x in item.claims['P569']]) or item.claims.get('P497'):
                match = False
                try:
                    item.removeClaims(item.claims['P39'][0])
                except:
                    pass
                if 'name' in person['party'][0]:
                    party = get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
                else:
                    party = get_qnumber(wikiarticle=person['party'], lang="zh-tw")
                for q_id in get_qnumber(wikiarticle=name, lang="zh-tw", limit=None):
                    print(q_id)
                    item = pywikibot.ItemPage(wikidata_site, q_id)
                    item.get()
                    if item.claims.get('P569'):
                        if b_target in [x.target for x in item.claims['P569']]:
                            match = True
                            break
                        if b_month == 1 and b_day == 1 and b_year in [x.target.year for x in item.claims['P569']]:
                            match = True
                            break
                    if item.claims.get('P102') and party in [x.target.id for x in item.claims['P102']]:
                        match = True
                        break
        else:
            q_ids = get_qnumber(wikiarticle=name, lang="zh-tw", limit=None)
            if len(q_ids) > 1:
                print(', '.join(q_ids))
                q_id = input('which one is correct?')
                if q_id:
                    item = pywikibot.ItemPage(wikidata_site, q_id)
                    item.get()
                    match = True
        if [x for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']] or not match:
            raise UnboundLocalError
        if item.claims.get('P569') and (person['election_year'] < x.target.year for x in item.claims['P569'][0].target.year or person['election_year'] > item.claims['P570'][0].target.year):
            raise UnboundLocalError
        print(name, item)
        input('...')
    except UnboundLocalError:
        labels = {"zh": person['name'], "zh-tw": person['name'], "zh-hant": person['name']}
        create = input('create new person?(y/n)')
        if create == 'y':
            item_id = create_item(wikidata_site, labels)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
        else:
            pass
    except KeyError:
        pass
    return item

def person_page_item_ko(person):
    site = pywikibot.Site("ko", "wikipedia")
    wikidata_site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    wikidata_repo = wikidata_site.data_repository()
    if person.get('wikidata_qid'):
        item = pywikibot.ItemPage(repo, person['wikidata_qid'])
        item.get()
        return item
    q_ids = get_qnumber(wikiarticle=person['name'], lang="ko", limit=None)
    try:
        if person.get('birth'):
            b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
            b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
            match, possible = False, []
            for q_id in q_ids:
                print(q_id)
                item = pywikibot.ItemPage(wikidata_site, q_id)
                item.get()
                # Q4167410 維基媒體消歧義頁, Q13406463 維基媒體列表條目
                if [x for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']] or not item.claims.get('P569'):
                    continue
                if b_target in [x.target for x in item.claims['P569']]:
                    match = True
                    break
                if b_year in [x.target.year for x in item.claims['P569']]:
                    possible.append(q_id)
        if not match:
            if possible:
                print(', '.join(possible))
                q_id = input('birth year matched, which one is correct?')
                if q_id:
                    item = pywikibot.ItemPage(wikidata_site, q_id)
                    item.get()
                    match = True
            if len(q_ids) > 1:
                print(', '.join(q_ids))
                q_id = input('which one is correct?')
                if q_id:
                    item = pywikibot.ItemPage(wikidata_site, q_id)
                    item.get()
                    match = True
            elif len(q_ids) == 1:
                item = pywikibot.ItemPage(wikidata_site, q_ids[0])
                item.get()
                match = True
        if [x for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']] or not match:
            raise UnboundLocalError
        print(person['name'], item)
    except UnboundLocalError:
        labels = {'ko': person['name']}
        for code in ['zh', 'zh-tw', 'zh-hant']:
            labels[code] = person['name_zh']
        if len(q_ids) != 0:
            create = input('create new person: %s?(y/n)' % person['name'])
        else:
            create = 'y'
        if create == 'y':
            item_id = create_item(wikidata_site, labels)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
        else:
            pass
    except KeyError:
        pass
    return item

def person_page_item_hk(person):
    site = pywikibot.Site("zh", "wikipedia")
    wikidata_site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    wikidata_repo = wikidata_site.data_repository()
    if person.get('wikidata_qid'):
        item = pywikibot.ItemPage(repo, person['wikidata_qid'])
        item.get()
        return item
    q_ids = get_qnumber(wikiarticle=person['name'], lang="zh", limit=None)
    try:
        match = False
        if len(q_ids) > 1:
            print(', '.join(q_ids))
            q_id = input('which one is correct?')
            if q_id:
                item = pywikibot.ItemPage(wikidata_site, q_id)
                item.get()
                match = True
        elif len(q_ids) == 1:
            item = pywikibot.ItemPage(wikidata_site, q_ids[0])
            item.get()
            match = True
        else:
            raise UnboundLocalError
        print(match)
        if [x for x in item.claims['P31'] if x.target.id in ['Q4167410', 'Q13406463']] or not match:
            raise UnboundLocalError
        if item.claims.get('P569') and (int(person['election_year']) < item.claims['P569'][0].target.year or int(person['election_year']) > item.claims['P570'][0].target.year):
            raise UnboundLocalError
        print(person['name'], item)
        input('...')
    except UnboundLocalError:
        labels = {"zh": person['name'], "zh-tw": person['name'], "zh-hant": person['name']}
        create = input('create new person?(y/n)')
        if create == 'y':
            item_id = create_item(wikidata_site, labels)
            item = pywikibot.ItemPage(repo, item_id)
            item.get()
        else:
            pass
    except KeyError:
        pass
    return item
