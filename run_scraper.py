# Python imports
import argparse
import json

# Local imports
from scraper.utils import *
from database.database import *
from scraper.scraper import Scraper

def add_universities(data):
  '''
  Create a new university in the university_info table.
  '''
  for id, university in data.items():
    try:
      create_university(int(id), university)
    except Error as e:
      print("Data could't be added.\n Please check the information.")

def run_scraper(to_update):
  university_dict = get_universities()
  print('Initializing Scraper...')
  scraper = Scraper()
  if not args.list:
    to_update = list(university_dict.keys())
  print('Universities to be updated:', [university_dict[id] for id in to_update])
  for id, university in university_dict.items():
    if id in to_update:
      data = scraper.make_update(university)
      scraper.save_into_db(university, id, data)
  print('Update Finished')

def show_universities():
  university_dict = get_universities()
  for id, university in university_dict.items():
    print(f'ID: {id} | {university}')

if __name__ == '__main__':
  initialize_database()
  parser = argparse.ArgumentParser()
  #subparsers = parser.add_subparsers()
  parser.add_argument("-sh", "--show", help="Show available universities",
                      required=False, action="store_true")
  add = parser.add_argument_group("add")
  add.add_argument("-a", "--add", help="Dictionary with universities to add", 
                   default=None, type=json.loads, required=False)

  scrape = parser.add_argument_group("scraper")
  scrape.add_argument("-s", "--scrape", help="Run scraper", required=False,
                      action="store_true")
  scrape.add_argument("-l", "--list", nargs='+', default=None, required=False,
                      help='"IDs list to scrape')

  args = parser.parse_args()
  if args.show:
    show_universities()
  
  if args.add:
    add_universities(args.add)
  elif args.scrape:
    if args.list:
      to_update = [int(id) for id in args.list]
    else:
      to_update = None
    run_scraper(to_update)