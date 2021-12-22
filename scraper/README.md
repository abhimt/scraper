# Scrapers

### Main Scraper

*class* Scraper()

It's in charge of call the particular scraper classes. It has two methods.

- `self.make_update(university_name) → data `:

​		This funcion creates an instance of a particular university scraper and scrapes the univeristy. It returns a dictionary with the 		scraped data.

- `self.save_into_db(university_name, university_id, data) → None `

  Compare and Merge the scraped data into the database. 

### University Scrapers

*class* ItuScraper()  →  IT University of Copenhagen

*class* DtuScraper() → Technical University of Denmark

*class* AarhusScraper() → Aarhus University

*class* KuScraper() → University of Copenhagen

*class* SduScraper() → University of Southern Denmark



The scraper classes can have different parameters but all must have the followings as pandas dataframes.

- `self.programs_info` : Contains all the programs dictated by the university.
- `self.programs_courses` : Contains the courses related to each program.
- `self.courses_info` : Contains the description of the course and the main program in which it's dictated. 



All scrapers have different methods that are particular according to the university webpage, you can find all the related methods inside the scritipts of each scraper class. Some general methods are stored in the `scraper/utils.py` file. There are five methods that are common for all the scraper classes:

- `self.update_programs_info()`

  Creates the `self.programs_info` dataframe.

- `self.update_programs_courses()`

  Creates the `self.programs_courses` dataframe.

- `self.update_courses_info()`

  Creates the `self.courses_info` dataframe.

- `self.update()`

  Runs a general scrape of the university filling all the dataframes.

- `self.export_data() → data` 

  Export the class dataframes as follows 

  ```python
  data = {'programs_info': programs_info,
          'courses_info': courses_info,
          'programs_courses': programs_courses}
  ```

