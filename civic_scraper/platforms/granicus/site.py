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
    def __init__(self, rss_url, cache=Cache()):
        self.url = rss_url
        self.granicus_instance = urlparse(rss_url).netloc.split('.')[0]
        self.cache = cache

    def create_asset(self, entry):
        asset_name = entry['title']
        committee_name, asset_type, str_datetime = asset_name.split(' - ')
        meeting_datetime = datetime.strptime(str_datetime, '%b %d, %Y %I:%M %p')

        meeting_url = entry['link']
        query_dict = parse_qs(urlparse(meeting_url).query)
        try:
            if 'ID' in query_dict.keys():
                meeting_id = 'granicus_{}_{}'.format(self.granicus_instance, query_dict['ID'][0])
            else:
                meeting_id = 'granicus_{}_{}'.format(self.granicus_instance, query_dict['MeetingID'][0])
        except KeyError:
            breakpoint()

        e = {'url': self.url,
             'asset_name': asset_name,
             'committee_name': committee_name,
             'place': None, # in Legistar, 'place' sometimes None; ok for all granicus 'place' missing?
             'state_or_province': None,
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

        parsed_rss = feedparser.parse(self.url)

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

        return parsed_rss
