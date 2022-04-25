import pytest
import logging
from civic_scraper.platforms import GranicusSite, GranicusJSONSite

logging.basicConfig(level="DEBUG")

granicus_rss_sites = [
    {'site': 'https://lacounty.granicus.com/ViewPublisherRSS.php?view_id=1&mode=agendas',
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
    # {'site': 'https://lacounty.granicus.com/services/archives/',
    #     'config': {
    #     'place': 'los_angeles',
    #     'state_or_province': 'ca',
    #     'start_date': '04/07/2019',
    #     'end_date': '06/12/2019'
    #     }
    # },
    {'site': 'https://lausd.granicus.com/services/archives/',
        'config': {
        'place': 'brookhaven',
        'state_or_province': 'ga',
        'start_date': '04/07/2019',
        'end_date': '06/12/2019'
        }
    },
]

def granicus_integration():
    # for obj in granicus_rss_sites:
    #     scraper = GranicusSite(obj['site'], **obj['config'])
    #     data = scraper.scrape()
    #     assert len(data) > 0

    for obj in granicus_json_sites:
        scraper = GranicusJSONSite(obj['site'], **obj['config'])
        data = scraper.scrape()
        assert len(data) > 0

if __name__ == '__main__':
    granicus_integration()
