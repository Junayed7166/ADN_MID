import psycopg2
import pandas as pd
import csv
import matplotlib.pyplot as plt

import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import re

# establishing the database connection
conn = psycopg2.connect(
   database="dse_database", user='postgres', password='123456', host='127.0.0.1', port= '5432'
)
conn.autocommit = True
#Creating a cursor object using the cursor() method
cursor = conn.cursor()



url = "https://www.dsebd.org/company_listing.php"
page = requests.get(url)
soup = BeautifulSoup(page.content, "html.parser")

all_body_content = soup.find_all("div", {"class": "BodyContent"})

company_list = []

for com in all_body_content:
  code = com.find_all("a")
  for only_code in code:
    #print(only_code.text.strip())
    company_list.append(only_code.text.strip())

company_list = [x for x in company_list if not x.startswith("TB")]
company_list = [x for x in company_list if not x.startswith("More...")]

def scrap_other_info(r,company,other_info_table):
  print(r)
  try:
    row = other_info_table.find_all('tr')[r]
    cells = row.find_all('td')
    date = cells[0].text.strip()

    pattern = r'\b\w{3} \d{2}, \d{4}\b'

    # Search for the date pattern in the text
    match = re.search(pattern, date)
    if match:
      date = match.group()
      data = cells[1].text.strip()
      #print(date)
      # print(data)
      sponsor_director_pattern = r'Sponsor/Director:\s+([\d.]+)'
      govt_pattern = r'Govt:\s+([\d.]+)'
      institute_pattern = r'Institute:\s+([\d.]+)'
      foreign_pattern = r'Foreign:\s+([\d.]+)'
      public_pattern = r'Public:\s+([\d.]+)'

      # Find the matches using regex
      sponsor_director_match = re.findall(sponsor_director_pattern, data)
      govt_match = re.findall(govt_pattern, data)
      institute_match = re.findall(institute_pattern, data)
      foreign_match = re.findall(foreign_pattern, data)
      public_match = re.findall(public_pattern, data)

      # Extract the values from the matches and convert them to float
      sponsor_director_values = [float(value.strip()) for value in sponsor_director_match]
      govt_values = [float(value.strip()) for value in govt_match]
      institute_values = [float(value.strip()) for value in institute_match]
      foreign_values = [float(value.strip()) for value in foreign_match]
      public_values = [float(value.strip()) for value in public_match]

    
      List = [company,date,*sponsor_director_values,*govt_values,*institute_values,*foreign_values,*public_values]
      #print(List)
      return List
    # elif not match:
    #   return
      #print("Date not found")
      
  except Exception as e:
    # Handle any other exceptions
    print("An error occurred:", str(e))
    

  
#-------------------------------------------------------------------------------------------------
company_details = []
other_info = []
for company in company_list:
  row_data = []
  com_url = "https://www.dsebd.org/displayCompany.php?name="+company
  page = requests.get(com_url)
  #print(company)
  soup = BeautifulSoup(page.content, "html.parser")
  #print(soup)

  compnay_name_h2 = soup.find('h2', {'class': 'BodyHead'})
  #print(compnay_name_h2)
  compnay_name = compnay_name_h2.text.strip()[compnay_name_h2.text.strip().find(": ") + len(": "):]
  row_data.append(compnay_name)
  #print(compnay_name)

  compnay_name_table = soup.find('table', {'class': 'shares-table'})
  for row in compnay_name_table.find_all('tr'):
    for cell in row.find_all(['th']):
        index = cell.text.strip().find(": ")
        substring = cell.text.strip()[index + len(": "):]
        row_data.append(substring)

  tables = soup.find_all('div', {'class': 'table-responsive'})
  sector_table_info = tables[2]
  r = sector_table_info.find_all('tr')[3]
  cells = r.find_all('td')
  sector = cells[1].text.strip()
  row_data.append(sector)
  
  company_details.append(row_data)
  #print(row_data)

  #tables = soup.find_all('div', {'class': 'table-responsive'})
  other_info_table = tables[9]

  for num in [3, 5, 7]:
      row = []
      l = scrap_other_info(num,company,other_info_table)
      other_info.append(l)
  #print(other_info)
  
other_info = [value for value in filter(None, other_info)]

company_details_df = pd.DataFrame(company_details, columns =['Company Name', 'Trading Code','Scrip Code','Sector'])
# columns_to_drop = company_details_df[['g1', 'g2']] 
# company_details_df = company_details_df.drop(columns=columns_to_drop)

company_info_df = pd.DataFrame(other_info, columns =['Trading Code', 'Date','Sponsor/Director','Govt','Institute','Foreign','Public'])

  
file_path = 'company_details_info.csv'
company_details_df.to_csv(file_path, index=False)

file_path = 'company_info.csv'
company_info_df.to_csv(file_path, index=False)

# --------------------------------------------------------
# Enter Data into the Database
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Company_Details(CompanyName VARCHAR(100),TradingCode VARCHAR(50), ScripCode CHAR(5), Sector VARCHAR(100))
    """)
with open("company_details_info.csv","r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        cursor.execute(
            "INSERT INTO Company_Details VALUES (%s,%s,%s,%s)",
            row
        )
print("Data Inserted in Company_Details Table Successfully")

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Company_Other_info(TradingCode VARCHAR(50),Date VARCHAR(30), SponsorDirector DECIMAL(10,2), Govt DECIMAL(10,2), Institute DECIMAL(10,2), ForeignNum DECIMAL(10,2), Public DECIMAL(10,2))
    """)
with open("company_info.csv","r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        cursor.execute(
            "INSERT INTO Company_Other_info VALUES (%s,%s,%s,%s,%s,%s,%s)",
            row
        )
print("Data Inserted in Company_Other_info Table Successfully")