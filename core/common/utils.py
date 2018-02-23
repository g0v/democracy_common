#!/usr/bin/python3
import requests
import pywikibot


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
        if item.claims['P31'][0].target.id == 'Q4167410': # Q4167410 維基媒體消歧義頁
            try:
                item.removeClaims(item.claims['P39'][0])
            except:
                pass
            party = get_qnumber(wikiarticle=person['party'][0]['name'], lang="zh-tw")
            b_year, b_month, b_day = [int(x) for x in person['birth'].split('-')]
            b_target = pywikibot.WbTime(year=b_year, month=b_month, day=b_day, precision='day')
            for q_id in get_qnumber(wikiarticle=name, lang="zh-tw", limit=None):
                item = pywikibot.ItemPage(wikidata_site, q_id)
                item.get()
                if item.claims.get('P569') and item.claims['P569'][0].target == b_target:
                    break
                if item.claims.get('P102') and item.claims['P102'][0].target.id == party:
                    break
        print(name, item)
    except UnboundLocalError:
        labels = {"zh": person['name'], "zh-tw": person['name']}
        item_id = create_item(wikidata_site, labels)
        item = pywikibot.ItemPage(repo, item_id)
        item.get()
    except KeyError:
        pass
    return item
