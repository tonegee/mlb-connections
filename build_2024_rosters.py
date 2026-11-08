#!/usr/bin/env python3
"""Build an MLB Connections dataset from date-specific MLB active roster snapshots.

Usage: python build_2024_rosters.py --start 2024-07-01 --end 2024-07-01
Full regular-season sampling: python build_2024_rosters.py --start 2024-03-20 --end 2024-09-29

This script fails closed if any requested roster snapshot cannot be retrieved.
The source records are daily snapshots, not inferred season-long tenures.
"""
import argparse
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request

BASE = 'https://statsapi.mlb.com/api/v1'

def fetch(path, params, cache_dir):
    url = BASE + path + '?' + urllib.parse.urlencode(params)
    key = path.strip('/').replace('/', '_') + '_' + urllib.parse.urlencode(params).replace('&', '_').replace('=', '-')
    cache = cache_dir / (key + '.json')
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    req = urllib.request.Request(url, headers={'User-Agent': 'MLBConnectionsRosterResearch/0.1', 'Accept': 'application/json'})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                obj = json.load(response)
            cache.write_text(json.dumps(obj, ensure_ascii=False), encoding='utf-8')
            time.sleep(0.2)
            return obj
        except Exception as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f'Failed to fetch {url}: {last}')

def dates(start, end):
    day = start
    while day <= end:
        yield day.isoformat()
        day += dt.timedelta(days=1)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', default='2024-07-01')
    p.add_argument('--end', default='2024-07-01')
    p.add_argument('--output', default='mlb-connections-2024.json')
    p.add_argument('--cache', default='mlb_roster_cache')
    args = p.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    if start.year != 2024 or end.year != 2024 or end < start:
        p.error('Choose an ordered date range entirely within 2024.')
    cache = pathlib.Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    teams = fetch('/teams', {'sportId': 1, 'season': 2024}, cache).get('teams', [])
    teams = [t for t in teams if t.get('league', {}).get('id') in (103, 104)]
    if len(teams) != 30:
        raise RuntimeError(f'Expected 30 AL/NL teams; received {len(teams)}. No output written.')
    players = {}
    observations = {}
    count = 0
    for date in dates(start, end):
        for team in teams:
            tid = team['id']
            payload = fetch(f'/teams/{tid}/roster', {'rosterType': 'active', 'date': date, 'season': 2024}, cache)
            roster = payload.get('roster')
            if not isinstance(roster, list) or not roster:
                raise RuntimeError(f'No active roster for {team["name"]} on {date}; cannot safely infer coverage. No output written.')
            for entry in roster:
                person = entry.get('person', {})
                pid, name = person.get('id'), person.get('fullName')
                if not pid or not name:
                    raise RuntimeError(f'Incomplete player record for {team["name"]} on {date}')
                sid = str(pid)
                players[sid] = {'id': sid, 'name': name}
                observations[(sid, str(tid), date)] = {
                    'playerId': sid, 'clubId': str(tid), 'clubName': team['name'],
                    'start': date, 'end': date,
                    'source': f'MLB Stats API active roster snapshot: {BASE}/teams/{tid}/roster?rosterType=active&date={date}&season=2024'
                }
            count += 1
        print(f'Completed {date}: {count} team/date snapshots', flush=True)
    result = {'players': sorted(players.values(), key=lambda x: (x['name'], x['id'])),
              'stints': sorted(observations.values(), key=lambda x: (x['start'], x['clubId'], x['playerId']))}
    pathlib.Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {args.output}: {len(players)} players, {len(observations)} dated roster observations')
    print('CAUTION: Daily snapshots are point-in-time evidence. They do not prove unsampled days or guarantee API archival completeness.')

if __name__ == '__main__':
    main()
