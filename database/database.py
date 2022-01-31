import sqlite3
from sqlite3.dbapi2 import Error
import pandas as pd

def create_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
      db_file = './database/courses.sql'
      conn = sqlite3.connect(db_file)
      return conn
    except Error as e:
      print(e)
    return conn

def execute_query(conn, query):
  try:
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
  except NameError as err:
    print(f"Error: '{err}'")

def initialize_database(verbose=False):
  db_file = './database/courses.sql'
  conn = sqlite3.connect(db_file)
  create_university_info = ('''CREATE TABLE IF NOT EXISTS university_info(
                              id int UNIQUE PRIMARY KEY,
                              university varchar UNIQUE);''')
  create_programs_info = ('''CREATE TABLE IF NOT EXISTS programs_info(
                            program varchar,
                            university_id varchar,
                            grade varchar,
                            PRIMARY KEY (program, university_id),
                            FOREIGN KEY (university_id) 
                            REFERENCES university_info(id));''')
  create_course_info = ('''CREATE TABLE IF NOT EXISTS courses_info(
                          course text NOT NULL,
                          program text NOT NULL,
                          university_id int NOT NULL,
                          description text NOT NULL,
                          PRIMARY KEY(course, program, university_id),
                          FOREIGN KEY (university_id)
                          REFERENCES university_info(university_id),
                          FOREIGN KEY (program) 
                          REFERENCES programs_info(program));''')
  create_programs_courses = ('''CREATE TABLE IF NOT EXISTS programs_courses(
                                program int NOT NULL,
                                course text NOT NULL,
                                university_id text NOT NULL,
                                FOREIGN KEY (course) 
                                REFERENCES courses_info(course),
                                FOREIGN KEY (university_id) 
                                REFERENCES university_info(university_id),
                                FOREIGN KEY (program) 
                                REFERENCES programs_info(program));''')
  execute_query(conn, create_university_info)
  execute_query(conn, create_programs_info)
  execute_query(conn, create_course_info)
  execute_query(conn, create_programs_courses)
  if verbose:
    print('Database successfully connected')

def create_university(id, university):
  conn = create_connection()
  cur = conn.cursor()
  sql = '''INSERT INTO university_info(id, university) VALUES(?,?)'''
  cur.execute(sql, (id, university))
  conn.commit()
  conn.close()
  print('University Added')

def get_universities():
  conn = create_connection()
  cur = conn.cursor()
  query = 'SELECT * FROM university_info'
  cur.execute(query)
  rows = cur.fetchall()
  university_dict = {}
  for row in rows:
    university_dict[row[0]] = row[1]
  return university_dict

# Scraper Functions

def query_university_info(university_id):
  '''Query the data in the database of a university
  INPUT:
  - university_id: name of the university to retrieve the data
  OUTPUT:
  - dataframes: dictionary with dataframes of each table in the database that
    corresponds to the university.
  '''
  conn = create_connection()
  data = {}
  tables = ['programs_info', 'courses_info', 'programs_courses']
  cur = conn.cursor()
  for table in tables:
    query = cur.execute(f'SELECT * FROM {table} WHERE university_id=?',
                        (university_id,))
    cols = [column[0] for column in query.description]
    data[table] = pd.DataFrame.from_records(data=cur.fetchall(), columns=cols)
    data[table]['university_id'] = data[table]['university_id'].astype('int64')
  conn.close()
  return data

def compare_and_merge(new_dataframe, old_dataframe):
  '''Compare two dataframes and merge their data'''
  df = pd.merge(new_dataframe, old_dataframe, how='outer', indicator='Exist',
                copy=False)
  added_elements = len(df[df['Exist']=='left_only'])
  print('%d new elements found and successfully merged' % added_elements)
  return df.drop(columns='Exist')

def update_table(table, university_id, df):
  '''Save new data into a dataframe avoiding duplicates. It eliminates the 
  old data and save the new df.
  INPUT:
  - table: table to update
  - university_id: university to update
  - df: dataframe with the new data
  '''
  conn = create_connection()
  cursor = conn.cursor()
  delete_query = f'DELETE FROM {table} WHERE university_id=?'
  cursor.execute(delete_query, (university_id,))
  conn.commit()
  df.to_sql(table, conn, if_exists='append', index=False)
  conn.commit()
  conn.close()
  print(f'{table} updated')

def update_university(university, university_id, data):
  '''
  INTPUT:
  - university: university to be updated
  - data: dictionary with the new data
  '''
  tables = ['programs_info', 'courses_info', 'programs_courses']
  old_data = query_university_info(university_id)
  for table in tables:
    new_dataframe = data[table]
    old_dataframe = old_data[table]
    updated_df = compare_and_merge(new_dataframe, old_dataframe)
    update_table(table, university_id, updated_df)
  print(f'{university} updated')

# NLP interface functions

def get_courses(program, university_id):
  conn = create_connection()
  query = f'SELECT * FROM programs_courses WHERE program==\'{program}\' AND university_id==\'{university_id}\''
  return pd.read_sql_query(query, conn)

def get_course_description(course, university_id):
  conn = create_connection()
  cur = conn.cursor()
  query = ''' SELECT description FROM courses_info WHERE
    course==?
    AND university_id==?
  '''
  output = ''
  cur.execute(query, (course, university_id,))
  rows = cur.fetchall()
  for row in rows:
    output += '{} '.format(row[0])
  return output

def get_program_list(university_id):
  conn = create_connection()
  cur = conn.cursor()
  query = '''SELECT program FROM programs_info WHERE university_id==?'''
  cur.execute(query, (university_id,))
  rows = cur.fetchall()
  programs = []
  for row in rows:
    programs.append(row[0])
  return programs

def select_programs (university):
  conn = create_connection()
  cur = conn.cursor()
  query = '''SELECT * FROM programs_courses WHERE university_id==?'''
  cur.execute(query, (university,))
  rows = cur.fetchall()
  return rows

def select_programs_courses (university):
    conn = create_connection()
    cur = conn.cursor()
    query = '''SELECT * FROM courses_info WHERE university_id=?'''
    cur.execute(query, (university,))
    rows = cur.fetchall()
    return rows

def add_sort_des(university, course, des):
  conn = create_connection()
  cur = conn.cursor()
  query = '''UPDATE courses_info SET short_des=? WHERE university_id=? AND course=?'''
  cur.execute(query, (des, university, course))
  conn.commit()