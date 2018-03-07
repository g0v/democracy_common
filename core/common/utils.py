#!/usr/bin/python3
import requests
import pywikibot


def aborigine_id(text):
    return {
        '平地原住民': 'Q50355511',
        '山地原住民': 'Q50355510'
    }[text]

def ordinal_numbers(number):
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
    resp = requests.get('https://www.wikidata.org/w/api.php', params=params).json()
    if resp.get('search') and limit:
        return resp['search'][0]['id']
    else:
        return [x['id'] for x in resp['search']]

def create_item(site, label_dict):
    new_item = pywikibot.ItemPage(site)
    new_item.editLabels(labels=label_dict)
    return new_item.getID()

def person_page_item(person):
    site = pywikibot.Site("zh", "wikipedia")
    wikidata_site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    wikidata_repo = wikidata_site.data_repository()
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
        # Q4167410 維基媒體消歧義頁, Q13406463 維基媒體列表條目
        if item.claims['P31'][0].target.id in ['Q4167410', 'Q13406463']:
            try:
                item.removeClaims(item.claims['P39'][0])
            except:
                pass
            if 'name' in person['party'][0]:
                party = get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
            else:
                party = get_qnumber(wikiarticle=person['party'], lang="zh-tw")
            b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
            b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
            b_year_target = pywikibot.WbTime(year=b_year, precision='year')
            match = False
            for q_id in get_qnumber(wikiarticle=name, lang="zh-tw", limit=None):
                item = pywikibot.ItemPage(wikidata_site, q_id)
                item.get()
                if item.claims.get('P569'):
                    if item.claims['P569'][0].target == b_target:
                        match = True
                        break
                    if b_month == 1 and b_day == 1 and item.claims['P569'][0].target.year == b_year:
                        match = True
                        break
                if item.claims.get('P102') and item.claims['P102'][0].target.id == party:
                    match = True
                    break
        if item.claims['P31'][0].target.id in ['Q4167410', 'Q13406463'] or not match:
            raise UnboundLocalError
        print(name, item)
    except UnboundLocalError:
        labels = {"zh": person['name'], "zh-tw": person['name'], "zh-hant": person['name']}
        item_id = create_item(wikidata_site, labels)
        item = pywikibot.ItemPage(repo, item_id)
        item.get()
    except KeyError:
        pass
    return item
