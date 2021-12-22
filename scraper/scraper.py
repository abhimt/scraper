# Local imports
from scraper.utils import *
from database.database import *

from scraper.ku_scraper import KuScraper
from scraper.itu_scraper import ItuScraper
from scraper.dtu_scraper import DtuScraper
from scraper.aarhus_scraper import AarhusScraper
from scraper.sdu_scraper import SduScraper
from scraper.cbs_scraper import CbsScraper

class Scraper():
  def __init__(self):
    self.scrapers = {
      'IT University of Copenhagen': ItuScraper(),
      'Technical University of Denmark': DtuScraper(),
      'Aarhus University': AarhusScraper(),
      'University of Copenhagen': KuScraper(),
      'University of Southern Denmark': SduScraper(),
      'Copenhagen Business School': CbsScraper()
    }

  def make_update(self, university_name):
    '''
    Update the programs dictated by the university
    - university_name
    1. retrieve information from the database
    2. make update of the subscraper
    3. compare and merge
    4. add new content to the dataset, here check that the data is not twice
    '''
    scraper = self.scrapers[university_name]
    print('#'*10)
    print('Scraping university:', university_name)
    scraper.update()
    data = scraper.export_data()
    return data

  def save_into_db(self, university_name, university_id, data):
    print('Saving data into database')
    update_university(university_name, university_id, data)
    print(f'Update Finished: University {university_name}')
