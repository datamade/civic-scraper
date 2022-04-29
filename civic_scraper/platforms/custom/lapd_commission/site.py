import re
import lxml.html
from time import sleep
from datetime import datetime
from urllib.parse import urlparse
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


class LAPDCommissionSite(base.Site):

    def __init__(self, url, cache=Cache()):

        self.url = url
        self.cache = cache

        self.session = Session()
        self.session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"

        # Raise an error if a request gets a failing status code
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }

    def _get_meeting_date(self, title):

        pattern = r'([a-z,A-z]*)\s?(\d{1,2}),?\s?(\d{4})'
        match = re.match(pattern, title)
        month, day, year = match.group(1), match.group(2), match.group(3)

        return datetime.strptime(f'{month} {day}, {year}','%B %d, %Y').date()

    def create_asset(self, title, agenda_url):

        meeting_date = self._get_meeting_date(title)
        meeting_id = meeting_date.strftime('lapd_commission_%m_%d_Y')

        e = {
            "url": agenda_url,
            "asset_name": title,
            "committee_name": 'LAPD Commission',
            "place": 'los_angeles',
            "state_or_province": 'ca',
            "asset_type": "Meeting",
            "meeting_date": meeting_date,
            "meeting_time": '',
            "meeting_id": meeting_id,
            "scraped_by": f'civic-scraper_{civic_scraper.__version__}',
            "content_type": 'pdf',
            "content_length": None,
        }

        return Asset(**e)

    def _get_meeting_id(self, object_id):

        pattern = r'http[s]?:\/\/[www.]?(\S*).primegov.com\/[\S]*'
        match = re.match(pattern, self.url)
        return f'primegov_{match.group(1)}_{object_id}'


class LAPDCommisionLandingSite(LAPDCommissionSite):

    def scrape(self):

        ac = AssetCollection()
        response = self.session.get(self.url)
        landing_page_tree = lxml.html.fromstring(response.text)

        agenda_element = landing_page_tree.xpath(
            '//main//section[contains(@class,"related-links")][1]//a[1]'
        )
        agenda = agenda_element[0]
        ac.append(self.create_asset(agenda.text, agenda.attrib['href']))

        return ac


class LAPDCommissionArchiveSite(LAPDCommissionSite):

    def __init__(self, url, start_date=None, end_date=None, cache=Cache()):

        self.start_date = datetime.strptime(start_date, '%m/%d/%Y')
        self.end_date = datetime.strptime(end_date, '%m/%d/%Y')
        super().__init__(url, cache)

    def archive_year_agendas(self, archive_year_url):

        year_page = self.session.get(archive_year_url)
        year_page_tree = lxml.html.fromstring(year_page.text)
        agenda_elements = year_page_tree.xpath(
            '//main//section[contains(@class,"related-links")]//div[@class="container"]//a'
        )
        
        for agenda in agenda_elements:
            if 'Public Comments' in agenda.text:
                continue

            meeting_date = self._get_meeting_date(agenda.text)
            if meeting_date > self.end_date.date():
                continue
            elif meeting_date < self.start_date.date():
                return

            yield agenda

    def scrape(self):

        ac = AssetCollection()

        response = self.session.get(self.url)
        archives_page_tree = lxml.html.fromstring(response.text)

        archive_years_elements = archives_page_tree.xpath(
            '//section[@class="cmn-table"]//div[@class="container"]//a'
        )
        archive_years_urls = map(
            lambda e: (e.text, e.attrib['href']), archive_years_elements
        )

        for year, url in archive_years_urls:
            # agendas are grouped by year
            if int(year) > self.end_date.year:
                continue
            elif int(year) < self.start_date.year:
                break

            for agenda in self.archive_year_agendas(url):
                ac.append(self.create_asset(agenda.text, agenda.attrib['href']))

            sleep(1)

        return ac
