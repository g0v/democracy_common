#!/usr/bin/python3
from requests import get
import pywikibot

from common import db_settings


def get_qnumber(wikiarticle, lang):
    resp = get('https://www.wikidata.org/w/api.php', params={
        'action': 'wbsearchentities',
        'search': wikiarticle,
        'language': lang,
        'uselang': lang,
        'format': 'json',
        'limit': 1,
        'type': 'item'
    }).json()
    if resp.get('search'):
        return resp['search'][0]['id']

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
name = get_qnumber(wikiarticle='賴士葆', lang="zh-tw")
print(name)
item = pywikibot.ItemPage(site, name)
item.get()
