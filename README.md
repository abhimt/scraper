# Course Summarization

## Overview

This repo aims to summarize university courses description to help students  writting their profile description. 
The project consist on two main parts, on the one hand we have the data collection tool which scraps the Danish universities searching for the programs they offer, the courses of those programs and the description of those courses. 
On the other hand we have a summarizer which using as input course descriptions  stored on the database, returns summaries of them.

The scraper is based on the selenium and beautifulsoup libraries. To use Selenium, it's necessary to install a browser driver that will be detailed in the Installation section. Selenium was particularly usefull to interact with the dynamic websites of some universities. The database is build over the sql. The library used to interact with it from python was sqlite3. The summarization tool is based on the transformers library from hugging-face and sentencepiece is used to tokenize
the input data.

Some of the challenges faced in the project are the non-standirized websites within the same universities that makes data collection more time-consuming. For this reason, the database is one of the improvements that could be done in a short time, recolecting more data.

## Table of Contents

[TOC]

## Repo Structure
- [`database`](): Contains the database and the functions associated to it
- [`scraper`](): Scripts to scrap the universities
- [`model`](): Scripts to obtain the summaries

## Installation

Here I detailed the installation for an Ubuntu os. For other os you can find the 
instructions on the [selenium official documentation](https://selenium-python.readthedocs.io/installation.html).
```
// Requirements
! pip install -r ~/coruse_summarization/requirements.txt

// Installing the browser driver
! apt-get update
! apt install chromium-chromedriver
! cp /usr/lib/chromium-browser/chromedriver /usr/bin
```

## Using the Project

**To make everything run smoothly it is highly recommended to keep the original folder structure of this repo!**
Each *.py in the root of the project has command line options. You can check them
all using:

```
python3 <script_name.py> -h
```

### Scraper
To run the scraper just run the following command on the root folder of the project.
```
$ python3 run_scraper.py -s
```

There are some optional parameters:

- List of ID's `-l `:  updates only the selected universities by ID's.
- Show `-sh`: Show the available scrapers
- Add `-a '{"ID":"university"}'` : manually add universities.

You can check the design of the scrapers in the [Scrapers Documentation](https://github.com/israfelsr/course_summarization/blob/master/scraper/README.md).

### Summarizer

#### Running the Summarizer

To run the summarizer it's necessary to enter the following parameters:

````
$ python3 summarize.py -u [university_id] -pr [program_id] -cl [courses_list] -p -s -n 'summaries.txt'
````

Where:

- University id `-u` : ID of the selected university
- Program id `-pr` : ID of the selected program
- Courses ID's list `-cl`: List of courses ID's separated by space

To visualize or save the output there are two optional arguments:

- Print to terminal `-p`
- Save `-s`: This needs the name of the file using `-n`. By default it saves at `./summarization/results`, you can modify this path using `-d`

#### Display the database

This script also allows special arguments. `-sh` show allows to navigate the database. Using the same commands `-u` and `-pr`  as options we can get the available programs for a given university and the available courses for a given program in that university.

An example of use is shown in the code block below.

```
$ python3 summarize.py -sh                                                   
ID: 1 | IT University of Copenhagen
ID: 2 | Technical University of Denmark
ID: 3 | Aarhus University
ID: 4 | University of Copenhagen
ID: 5 | University of Southern Denmark

$ python3 summarize.py -sh -u 1
Showing the programs of the university IT University of Copenhagen:
0 : bsc data science
1 : bsc digital design and interactive technologies
2 : bsc global business informatics
3 : bsc software development
4 : msc computer science
5 : msc data science
6 : msc digital design and interactive technologies
7 : msc digital innovation and management
8 : msc games
9 : msc software design

$ python3 summarize.py -sh -u 1 -pr 0
University: IT University of Copenhagen
Showing available courses for the program: bsc data science
0 : algorithms and data structures
1 : algorithms and data structures bsc (summer university)
2 : applied statistics
3 : data visualisation and data driven decision making
4 : first year project
5 : introduction to database systems ds
6 : large scale data analysis
7 : reflections on data science
8 : second year project (introduction to natural language processing and deep learning)
9 : data science in research business and society
10 : introduction to data science and programming
11 : linear algebra and optimisation
12 : machine learning
13 : network analysis
14 : operating systems and c
15 : security and privacy
16 : software development and software engineering
17 : technical communication
```

## Tests and Samples

In this section I will show a little example of the use of the summarizer using  some of the data in the database. 
There is an automated test in the `summarize.py` script that can be called as follows.

```
$ python3 summarize.py -t
```

The test function selects automatically a university, a program and a selection courses as is shown below.

```
- University: IT University (ID: 1)
- Program: msc data science (ID: 0)
- Courses: [0, 4, 5, 7, 9, 10, 12]
```

Notice that this is exaclty the same as run:
```
$ python3 summarize.py -p -u 1 -pr 0 -cl 0 4 5 7 9 10 12
```

The result with the summary of the coures will be automatically printed in the command line and optionally can be saved as a text file. The summary of this selection is:

````
University: IT University of Copenhagen
Program: bsc data science

algorithms and data structures
This course provides the basic algorithmic tools indispensable for every software developer. Topics covered are among others complexity analysis, big-O, algorithmic problem solving techniques including divide-and-conquer, concrete algorithms and data structures for search trees, sorting, hashing, graphs, shortest paths. 

first year project
This course aims to familiarize students with the pipeline for Data Science projects. Students will formulate a domain-specific research question and translate it into a technicalproblem. The problem can then be addressed with techniques within Data Science. The course consists of a series of full-fledged Data Science mini-projects. 

introduction to database systems ds
The course covers fundamental techniques for developing data management and data analytics applications. The main part of the course deals with traditional relational database processing. In the latter part, the focus is on new developments for both traditional database applications and for modern data Analytics applications. After the course, the student should be able to:Write SQL queries, involving multiple relations, grouping, aggregation, and subqueries. 

reflections on data science
In this course you will learn to reflect on the use and societal implications of data, models and algorithms. How can we check that a claim based on data is plausible? What are the technical and societal consequences of using biased data to train our algorithms? We will explore these and other similar questions using real-world cases. 

data science in research business and society
The course is built around four modules exploring approaches to data science from different perspectives. Students will engage in weekly group activities producing content for a data journal. A selection of entries to the data journal will become the basis for their exam. After the course, the student should be able to: Account for different definitions of data, different data types and different research approaches that generate it. 

introduction to data science and programming
This course is an introduction to programming, data science and related foundations. There are 14 weeks of teaching activities. The lectures cover topics in Data Science, Python programming, and any Supplementary Mathematics (beyond Gymnasium Maths) The exercises are aimed at additionally equipping the students with the skill sets necessary for the successful completion of homework assignments. 

machine learning
This course gives a fundamental introduction to machine learning (ML) with an emphasis on statistical aspects. In the course, we focus on both the theoretical foundation for ML and the application of ML methods. The course will comprise around 10 weeks of lectures and exercise sessions and around 4 weeks of project work.
````

## Credits
This work was developed under the supervision of the [Excelerate Team]([https://excelerate.careers/](https://excelerate.careers/))

## License
[MIT](https://github.com/israfelsr/course_summarization/blob/main/LICENSE)