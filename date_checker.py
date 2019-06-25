#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""
Iterates through the XML files to check what text does not align with the encoded numerical date in the date tag
"""

from bs4 import BeautifulSoup
import pickle
import regex as re
import pandas as pd
from pandas import *
from processing_functions import remove_diacritic

date_regex = '(?:([0-9]{4})-([0-9]{1,2})-([0-9]{1,2}))'
# Finds the text that representst the numerical date
text_regex = '(?:([0-9]{1,2}(?:er)?)(?:[ ,.\n\r]+)([A-Za-z\(\) \n\r,.]+)(?:[ ,.\n\r]+)([0-9 ]{4,}))'
# Converts text to the month number
month_to_num = {'janvier':'01', 'fevrier':'02', 'mars':'03', 'avril':'04', 'mai':'05', 'juin':'06', 'juillet':'07', 'aout':'08', 'septembre':'09', 'octobre':'10', 'novembre':'11', 'decembre':'12'}
vol_regex = 'Docs\/(vol[0-9]{1,2}).xml'


def parseFiles():
	wrong_dates = set()
	files = os.listdir("Docs/")
	for filename in files:
		if filename.endswith(".xml"):
			print(filename)
			filename = open('Docs/' + filename, "r")
			volno = re.findall(vol_regex, str(filename))[0]
			contents = filename.read()
			soup = BeautifulSoup(contents, 'lxml')
			# A search for date tags that contain a valid value
			dates = soup.find_all('date')
			for date in dates:
				if date.attrs:
					coded_date = date['value']
					year, month, day = re.findall(date_regex, coded_date)[0]
					child = date.findChildren()
					if child:
						child[0].extract()
					text_date = date.get_text()
					text_date = re.sub(r'([ ]{2,})', ' ', text_date)
					text_date = remove_diacritic(text_date).decode('utf-8')
					text_date = text_date.lower().replace('\n','')
					# Various checks perfomed to see if the textual date matches the encoded date or is valid at all
					try:
						text_day, text_month, text_year = re.findall(text_regex, text_date)[0]
						text_month = text_month.replace(' (sic)','').replace('\n','').replace('\r','').replace(' ','')
						text_date = remove_diacritic(text_month).decode('utf-8')
						text_month = re.sub(r'([ ]{2,})', ' ', text_month)
					except:
						wrong_dates.add(coded_date + "; " + str(date.contents) + "; " + str(volno) + "\n")
					try:
						month_num = month_to_num[text_month]
					except:
						wrong_dates.add(coded_date + "; " + str(date.contents) + "; " + str(volno) + "\n")
					if (month_num != str(month)):
						wrong_dates.add(coded_date + "; " + str(date.contents) + "; " + str(volno) + "\n")
			filename.close()

	# Write the wrong dates to a file
	file = open('wrong_dates.txt', 'w')
	for item in sorted(wrong_dates):
		file.write(item)
	file.close()


if __name__ == '__main__':
    import sys
    parseFiles()