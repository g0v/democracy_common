import requests
import pandas as pd
import trio
import asks
import re
from collections import defaultdict


async def get(url):
    i = 1
    while True:
        try:
            return await asks.get(url)
        except Exception as e:
            print(f'GET {url} ERROR at {i}th try: {str(e)}')
            i += 1
            continue

async def get_second_tier_hierarchy():
    sido_addr = (await get('http://su.nec.go.kr/prg/sidoAddr/sidoAddrAjax.jsp?type=1')).json()
    hierarchy = defaultdict(lambda: {'children': []})
    for area in sido_addr:
        if area['lv'] == '1':
            hierarchy[area['idx']].update({
                'id': area['id'],
                'name': area['name'],
                'lv': 1,
            })
        if area['lv'] == '2':
            hierarchy[area['parent']]['children'].append({
                'id': area['id'],
                'name': area['name'],
                'lv': 2,
            })
    return hierarchy


PARENS_RE = re.compile(r'(.+)\(((?:[^,]+,)*[^,]+)\)')
TONG_DEF = r'(?:[0-9]+통?~[0-9]+통|[0-9]+통)'
TONG_RE = re.compile(f'([가-힣0-9·]*(?!통)[가-힣])\W*((?:{TONG_DEF}\W*)*{TONG_DEF})')
SI_GU_RE = re.compile(r'^(?P<si>[가-힣]+시)(?P<gu>[가-힣]+구)$')

def handle_tongs(raw_tongs):
    tong_groups = map(str.strip, raw_tongs.split())
    result = []
    for tong_group in tong_groups:
        start, end = re.match(r'(?:([0-9]+)통?~)?([0-9]+)통', tong_group).groups()
        if start is None:
            result.append(int(end))
        else:
            result.extend(range(int(start), int(end) + 1))
    return result


async def fetch_table(parents):
    sido_id = parents[0]['id']
    parent_names = tuple(p['name'] for p in parents)
    if len(parents) == 1:
        r = await get(f'http://{sido_id}.nec.go.kr/{sido_id}/sub4_5.jsp')
    elif len(parents) == 2:
        r = await get(f'http://{sido_id}.nec.go.kr/{sido_id}/{parents[1]["id"]}/sub1.jsp')
        si_gu_match = SI_GU_RE.match(parent_names[1])
        if si_gu_match:
            parent_names = parent_names[:1] + si_gu_match.groups()

    tables = pd.read_html(r.text, match='선거구')
    df = tables[1]
    if len(df) == 1 and df['선거구역'].str.endswith('일원').all():
        area = df.iloc[0]
        return [(area['선거구명'], [parent_names])]

    if df['선거구역'].str.startswith(parents[-1]['name']).all():
        df['선거구역'] = df['선거구역'].str.replace(f'{parents[-1]["name"]} ', '')

    df['선거구역'] = df['선거구역'].str.findall('[^,\(\)]+(?:\([^\)]+\))?')
    election_areas = []
    for i, row in df.iterrows():
        entry = (row['선거구명'], [])
        tong_match = re.match(TONG_RE, ','.join(row['선거구역']))
        if tong_match:
            subarea_name, raw_tongs = tong_match.groups()
            included_tongs = handle_tongs(raw_tongs)
            entry[1].append(parent_names + (subarea_name, included_tongs))
            continue
        for subarea in row['선거구역']:
            subarea = subarea.strip()
            parens_match = PARENS_RE.match(subarea)
            if parens_match:
                subarea_name, unit_subareas = parens_match.groups()
                if (subarea_name == '중앙탑면' and unit_subareas == '가금면') or \
                        (subarea_name == '중앙동' and unit_subareas == '진해구'):
                    entry[1].append(parent_names + (subarea,))
                    continue
                tong_match = re.match(TONG_RE, unit_subareas)
                if tong_match:
                    if row['선거구명'] == '세종특별자치시 제9선거구':
                        entry[1].append(parent_names + (subarea_name, '어진동'))
                    unit_subarea_name, raw_tongs = tong_match.groups()
                    included_tongs = handle_tongs(raw_tongs)
                    if unit_subarea_name != '종촌':
                        entry[1].append(parent_names + (subarea_name, unit_subarea_name, included_tongs))
                    else:
                        entry[1].append(parent_names + (subarea_name, included_tongs))
                    continue
                entry[1].extend([
                    tuple([*parent_names, subarea_name, *a.strip().split()])
                    for a in unit_subareas.split(',')
                ])
            else:
                entry[1].append(tuple([*parent_names, subarea]))
        election_areas.append(entry)
    return election_areas

async def main():
    hierarchy = await get_second_tier_hierarchy()
    election_areas = []
    async def run_fetch_table(*args):
        election_areas.extend(await fetch_table(*args))
        print(f'FINISHED {len(election_areas)}')
    async with trio.open_nursery() as nursery:
        for first_level_area in hierarchy.values():
            sido_id = first_level_area['id']
            lv_name = first_level_area['name'][-1]
            if not first_level_area['children']:
                nursery.start_soon(
                    run_fetch_table,
                    [first_level_area],
                )
            for second_level_area in first_level_area['children']:
                sla_id = second_level_area['id']
                nursery.start_soon(
                    run_fetch_table,
                    [first_level_area, second_level_area],
                )
    import json
    with open('result.json', 'w') as f:
        json.dump(election_areas, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    asks.init('trio')
    trio.run(main)
