import re
from time import sleep

import civic_scraper
import feedparser
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from datetime import datetime
from requests import Session
from pathlib import Path
from urllib.parse import urlparse, parse_qs


class GranicusSite(base.Site):
    def __init__(self, rss_url, place=None, state_or_province=None, cache=Cache()):
        self.url = rss_url
        self.granicus_instance = urlparse(rss_url).netloc.split('.')[0]
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

    def create_asset(self, entry):
        asset_name = entry['title']
        committee_name, asset_type, str_datetime = asset_name.split(' - ')
        meeting_datetime = datetime.strptime(str_datetime, '%b %d, %Y %I:%M %p')

        meeting_url = entry['link']
        query_dict = parse_qs(urlparse(meeting_url).query)

        # entries for a single granicus instance might use different query params
        if 'ID' in query_dict.keys():
            meeting_id = 'granicus_{}_{}'.format(self.granicus_instance, query_dict['ID'][0])
        else:
            meeting_id = 'granicus_{}_{}'.format(self.granicus_instance, query_dict['MeetingID'][0])

        e = {'url': self.url,
             'asset_name': asset_name,
             'committee_name': committee_name,
             'place': self.place,
             'state_or_province': self.state_or_province,
             'asset_type': asset_type,
             'meeting_date': meeting_datetime.date(),
             'meeting_time': meeting_datetime.time(),
             'meeting_id': meeting_id,
             'scraped_by': f'civic-scraper_{civic_scraper.__version__}',
             'content_type': 'txt',
             'content_length': None,
            }
        return Asset(**e)

    def scrape(self, download=True):
        session = Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"})

        response = session.get(self.url)
        parsed_rss = feedparser.parse(response.text)

        ac = AssetCollection()
        assets = [self.create_asset(e) for e in parsed_rss['entries']]
        for a in assets:
            ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=session)

        return ac


class GranicusJSONSite(base.Site):
    def __init__(self, url, committee_name_parser=None, place=None, state_or_province=None, start_date=None, end_date=None, view_id=None, cache=Cache()):
        self.url = url
        self.subdomain = urlparse(url).netloc.split('.')[0]
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache
        self.committee_name_parser = committee_name_parser

        self.start_date = datetime.strptime(start_date, '%m/%d/%Y')
        self.end_date = datetime.strptime(end_date, '%m/%d/%Y')
        self.view_id = view_id

    def _get_meeting_id(self, object_id):

        pattern = r'http[s]?:\/\/[www.]?(\S*).granicus.com\/[\S]*'
        match = re.match(pattern, self.url)
        return f'granicus-{match.group(1)}-{object_id}'

    def create_asset(self, entry, url):
        asset_name = entry['name']
        meeting_datetime = datetime.strptime(entry['date'], '%Y-%m-%d')
        meeting_id = self._get_meeting_id(entry['id'])

        e = {'url': url,
             'asset_name': asset_name,
             'committee_name': self.committee_name_parser(asset_name),
             'place': self.place,
             'state_or_province': self.state_or_province,
             'asset_type': 'Agenda',
             'meeting_date': meeting_datetime.date(),
             'meeting_time': '',
             'meeting_id': meeting_id,
             'scraped_by': f'civic-scraper_{civic_scraper.__version__}',
             'content_type': 'pdf',
             'content_length': None,
            }
        return Asset(**e)

    def _getMeetingDateObj(self, meeting):
        return datetime.strptime(meeting['date'], '%Y-%m-%d')

    def _getAgendaUrl(self, clip_id):
        return f'https://{self.subdomain}.granicus.com/AgendaViewer.php?view_id={self.view_id}&clip_id={clip_id}'

    def scrape(self):
        session = Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"})

        response = session.get(self.url)
        # add a date object to each meeting
        meetings = map(lambda m: dict(**m,**{'dateObj': self._getMeetingDateObj(m)}), response.json())

        seen = set() # e.g. spanish captioned meetings have same agenda
        agendas = AssetCollection()

        # we can't assume the response will be in 100% chronological order
        for meeting in sorted(meetings,reverse=True,key=lambda m: m['dateObj']):
            if meeting['dateObj'] > self.end_date:
                continue
            elif meeting['dateObj'] < self.start_date:
                break

            # some instances have test meetings with no url or upload name
            if not meeting['agendaurl'] and not meeting['agendauploadname']:
                continue

            if meeting['agendaurl']:
                if meeting['agendaurl'] not in seen:
                    agendas.append(self.create_asset(meeting, meeting['agendaurl']))
                    seen.add(meeting['agendaurl'])

                continue

            if meeting['agendauploadname'] and meeting['agendauploadname'] in seen:
                continue

            # if page redirects, there should be a pdf on the other side
            agenda_url = self._getAgendaUrl(meeting['id'])
            agenda_resp = session.get(agenda_url)
            if agenda_url != agenda_resp.url:
                agendas.append(self.create_asset(meeting, agenda_url))
                seen.add(meeting['agendauploadname'])

            sleep(1)

        return agendas
