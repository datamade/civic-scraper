import pytest
import logging
from civic_scraper.platforms import GranicusSite, GranicusJSONSite
from committee_name_parsers import la_county_committee_parser, la_usd_comittee_parser

logging.basicConfig(level="DEBUG")

granicus_rss_sites = [
    {'site': 'https://brookhavencityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {
        'place': 'brookhaven',
        'state_or_province': 'ga',
     },
    },
    {'site': 'https://eastpointcityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {
        'place': 'east_point',
        'state_or_province': 'ga',
     },
    },
    {'site': 'https://atlantacityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {
        'place': 'atlanta',
        'state_or_province': 'ga',
     },
    },
]

granicus_json_sites = [
    {'site': 'https://lacounty.granicus.com/services/archives/',
        'config': {
        'place': 'los_angeles',
        'state_or_province': 'ca',
        'start_date': '01/01/2022',
        'end_date': '12/31/2022',
        'view_id': 2,
        'committee_name_parser': la_county_committee_parser
        }
    },
    {'site': 'https://lausd.granicus.com/services/archives/',
        'config': {
        'place': 'los_angeles',
        'state_or_province': 'ca',
        'start_date': '01/01/2022',
        'end_date': '12/31/2022',
        'view_id': 1,
        'committee_name_parser': la_usd_comittee_parser
        }
    },
]

def granicus_integration():
    for obj in granicus_rss_sites:
        scraper = GranicusSite(obj['site'], **obj['config'])
        data = scraper.scrape()
        assert len(data) > 0

    for obj in granicus_json_sites:
        scraper = GranicusJSONSite(obj['site'], **obj['config'])
        data = scraper.scrape()
        assert len(data) > 0

if __name__ == '__main__':
    granicus_integration()
