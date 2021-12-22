# Python Imports
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm, trange

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# TODO: add the grade in the beggining of the program name

# Local Imports
from scraper.utils import *

class AarhusScraper():
  def __init__(self):
    self.home_url = 'https://kandidat.au.dk/en'
    self.university_name = 'Aarhus University'
    self.university_id = 3
    self.blacklist = ['public policy', 'visual anthropology',
                      'international master of biodiversity ecology and evolution',
                      'economics and business administration']
    self.economic_programs = ['business intelligence', 'finance', 'marketing',
    'business-to-business marketing and purchasing', 'information management',
    'commercial and retail management', 'finance and international business',
    'innovation management and business development', 'international business',
    'international business development', 'international economic consulting', 
    'management accounting and control', 'operations and supply chain analytics', 
    'strategic communication', 'strategy, organisation and leadership']
    self.language_programs = ['intercultural studies']

  def update_programs_info(self):
    browser = connect_to_browser()
    browser.get(self.home_url)
    cookies_reject = browser.find_element_by_id("cookiescript_reject")
    cookies_reject.click()
    language_tab = browser.find_element_by_class_name("db-button.button-4")
    language_tab.click()
    time.sleep(0.5)
    english_button = browser.find_elements_by_class_name("csc-header")
    press_element(english_button, 'english')
    programs_html = BeautifulSoup(browser.page_source, 'html.parser')
    collapsible_division = programs_html.find("div", "csc-frame au_collapsible")
    programs_webelement = collapsible_division.findAll('a')
    programs_name = []
    programs_url = []
    for program in programs_webelement:
      url = program["href"]
      if url in programs_url: continue
      program_name = _aarhus_program_processing(program.text)
      if program_name in self.blacklist: continue
      if "(only in danish)" in program_name: continue 
      # Save program data
      programs_name.append(program_name)
      programs_url.append(url)
    browser.quit()
    grade = ["msc"]*len(programs_name)
    data = {'program': programs_name, 'grade': grade, 'url': programs_url}
    self.programs_info = pd.DataFrame(data=data)

  def update_programs_courses(self):
    browser = connect_to_browser()
    browser.get(self.home_url)
    cookies_reject = browser.find_element_by_id("cookiescript_reject")
    cookies_reject.click()
    self.programs_courses = pd.DataFrame(columns=['program', 'course', 'url'])
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, _, program_url = self.programs_info.iloc[i]
      browser.set_window_size(800,800)
      browser.get(program_url)
      buttons = browser.find_elements_by_class_name("csc-header")
      for btn in buttons:
        if (btn.text == 'Programme structure') or (btn.text == 'Programme Structure'):
          btn.click()
      program_courses = []
      courses_url = []
      # Programs with different webpage
      if (program in self.language_programs) or (program in self.economic_programs):
        try:
          program_courses, courses_url = _extract_courses(browser, 
                                                         program_courses,
                                                         courses_url)
        except:
          #print("A problem ocurred in program:", program)
          #print(program_url)
          # TODO: See what's going on with these programs
          continue
      else:
        subprograms = browser.find_elements_by_tag_name("option")
        if len(subprograms) == 0:
          try:
            program_courses, courses_url = _extract_courses(browser,
                                                           program_courses,
                                                           courses_url)
          except:
            self.programs_info.loc[self.programs_info.program == program,
                                   'url'] = np.nan
            #print("A problem ocurred in program:", program)
            #print(program_url)
            # TODO: See what's going on with these programs
            continue
        else:
          for subprogram in subprograms:
            browser.execute_script("$(arguments[0]).click();", subprogram)
            #subprogram.click()
            program_courses, courses_url = _extract_courses(browser,
                                                           program_courses,
                                                           courses_url)
      program_list = [program]*len(program_courses)
      df = pd.DataFrame(data={'program':program_list, 'course':program_courses,
                              'url': courses_url})
      self.programs_courses = self.programs_courses.append(df)
    browser.quit()
    # TODO: See which courses we don't want on the list as 'master's thesis'

  def get_elective_descriptions(self, browser, course_url):
    browser.get(course_url)
    pages = browser.find_element_by_class_name("resetlist.au-pagination")
    next = pages.find_elements_by_tag_name("button")[-1]
    while True:
      cards = browser.find_elements_by_class_name('cc-listresult')
      for card in cards:
        card_title = card.find_element_by_tag_name("a")
        print(card_title.text.lower())
      if not next.is_enabled():
        break
      # CHANGE TO THE NEXT PAGE
      next.click()
      pages = browser.find_element_by_class_name("resetlist.au-pagination")
      next = pages.find_elements_by_tag_name("button")[-1]

  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'program', 'description'])
    browser = connect_to_browser()
    browser.get('http://kursuskatalog.au.dk/en/')
    cookies_button = browser.find_element_by_id("au_cookiesalert_yes")
    cookies_button.click()
    for i in trange(len(self.programs_courses), desc='Scraping courses description'):
      program, course_name, course_url = self.programs_courses.iloc[i]
      if 'electivegroups' in course_url: continue
      # TODO: add the electives to all the programs
      try:
        df = self.courses_info.loc[self.courses_info.course == course_name]
        if not df.empty:
          continue
        browser.get(course_url)
        WebDriverWait(browser, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cc-listresult")))
        cards = browser.find_elements_by_class_name('cc-listresult')
        if len(cards) > 2:
          print(course_url, course_name)
        card_link = _select_newest_card(cards)
        browser.get(card_link)
        course_html = BeautifulSoup(browser.page_source, 'html.parser')
        description_column = course_html.find("div", "au_coursecatalog_middle")
        text = description_column.find_all(text=True)
        output = ''
        for txt in text:
          blacklist = ["Description of qualifications", "Contents",
                      "Objectives of the course:", "Competences and skills:",
                      "Learning outcomes and competences:", 
                      "At the end of the course the student will be able to:", 
                      "The course will qualify the student to:"]
          if txt in blacklist:
            continue
          output += '{} '.format(txt)
        df = pd.DataFrame(data={'course':[course_name], 'program':[program],
                                'description':[output]})
        self.courses_info = self.courses_info.append(df)
      except:
        self.programs_courses.loc[(self.programs_courses.program == program) \
                                  & (self.programs_courses.course == course_name),
                                   'url'] = np.nan
        #print("A problem occured when extracting the data:")
        #print(course_name, course_url, program)
        # TODO: See how to solve these programs.
        continue
    # TODO: extract the description of elective courses
    # only_electives = self.programs_courses[self.programs_courses.course=='elective courses']
    # TODO: some courses have different name in the results.
    browser.quit()

  # AUTO SCRAPER
  def update(self):
    work_time = time.localtime()
    print('Starting update at {}:{}'.format(work_time.tm_hour, work_time.tm_min))
    print('This will take several minutes')
    self.update_programs_info()
    print('1/3 Updates Finished')
    self.update_programs_courses()
    print('2/3 Updates Finished')
    self.update_courses_info()
    print('3/3 Updates Finished')
    work_time = time.localtime()
    print('Finished at {}:{}'.format(work_time.tm_hour, work_time.tm_min))

  def export_data(self):
    programs_info = self.programs_info.drop(labels='url',
                                            axis=1).dropna().reset_index(drop=True)
    programs_info.insert(1, 'university_id', self.university_id)
    programs_courses = self.programs_courses[self.programs_courses.course!='elective courses']
    programs_courses = programs_courses.drop(labels='url', 
                                        axis=1).dropna().reset_index(drop=True)
    programs_courses.insert(2, 'university_id', self.university_id)
    courses_info = self.courses_info.reset_index(drop=True)
    courses_info.insert(2, 'university_id', self.university_id)
    data = {'programs_info': programs_info,
            'courses_info': courses_info,
            'programs_courses': programs_courses}
    return data

# AARHUS.UTILS
def _select_newest_card(cards):
  newest_period = 0
  card_link = None
  for card in cards:
    card_title = card.find_element_by_tag_name("a")
    properties = card.find_elements_by_tag_name("li")
    period = _aarhus_period_processing(properties[2].text)
    if (period > newest_period):
      newest_period = period
      card_link = card_title.get_attribute('href')
  return card_link

def _extract_courses(browser, program_courses, courses_url):
    program_html = BeautifulSoup(browser.page_source, 'html.parser')
    soup = program_html.find("div", "study-diagramme list show-for-small-only")
    soup = soup.find_all("a", target="_blank")
    blacklist = ["tlv", "profile", "master's thesis", "specialisation",
                 "elective courses"]
    for course in soup:
      course_name = course.text.lower()
      course_url = course["href"]
      if (course_name in program_courses) and (course_url in courses_url):
        continue
      if course_name in blacklist:
        continue
      if "master's thesis" in course_name:
        continue
      else:
        program_courses.append(course_name)
        courses_url.append(course_url)
    return program_courses, courses_url

def _aarhus_program_processing(program):
  program = program.lower()
  program = program.replace('(en)', '')
  program = program.replace('(da/en)', '')
  program = program.replace('(erasmus mundus)', '')
  program = program.replace('(herning)', '')
  program = program.replace('(eur-organic)', '')
  program = program.replace('(imabee)', '')
  program = program.replace('(double-degree)', '')
  program = program.replace('(double degree)', '')
  program = program.replace('(msc in engineering)', '')
  program = program.replace(', msc', '')
  program = program.replace(', cand.merc.', '')
  program = program.rstrip()
  program = program.lstrip()
  return program

def _aarhus_period_processing(period):
  period = period.lower()
  year = period[-4:]
  if "autumn" in period:
    period = int(year + '01')
  elif "spring" in period:
    period = int(year + '02')
  return period