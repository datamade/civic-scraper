import pytest
import logging
from civic_scraper.platforms import LAPDCommissionArchiveSite
from civic_scraper.platforms.custom.lapd_commission.site import LAPDCommisionLandingSite, LAPDCommisionLandingSite

logging.basicConfig(level="DEBUG")

archive = {
    'site': 'https://www.lapdonline.org/police-commission/police-commission-meetings-archives/',
    'config': {
        'start_date': '08/12/2020',
        'end_date': '02/04/2021'
    }
}

landing_site = 'https://www.lapdonline.org/police-commission/'

def lapd_commission_integration():
    archive_scraper = LAPDCommissionArchiveSite(archive['site'], **archive['config'])
    data = archive_scraper.scrape()
    assert len(data) > 0

    landing_site_scraper = LAPDCommisionLandingSite(landing_site)
    data = landing_site_scraper.scrape()
    assert len(data) > 0

if __name__ == '__main__':
    lapd_commission_integration()
