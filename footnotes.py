#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""
Iterates through all the speeches and pulls out the footnotes
"""

from bs4 import BeautifulSoup
import unicodedata
import os
import csv
import pickle
import regex as re
import pandas as pd
import numpy as np
from nltk import word_tokenize
from nltk.util import ngrams
import collections
from collections import Counter
import os
import gzip
from make_ngrams import compute_ngrams
import xlsxwriter
from processing_functions import remove_diacritic, load_speakerlist
from make_ngrams import make_ngrams
from parse_speaker_names import compute_speaker_Levenshtein_distance, read_names


#Seance followed by less than or equal to 4 line breaks (\n) then date value =
daily_regex = '(?:Séance[\s\S]{0,200}<date value=\")(?:[\s\S]+)(?:Séance[\s\S]{0,200}<date value=\")'
page_regex = '(?:n=\"([A-Z0-9]+)" id="[a-z0-9_]+")\/>([\s\S]{1,9000})<pb '
vol_regex = 'AP_ARTFL_vols\/AP(vol[0-9]{1,2}).xml'
footnote_regex = r'<note place="foot">[\w\W]+<\/note>'

speechid_to_speaker = {}
speakers_seen = set()
speaker_dists = []
speaker_dists_split = []
footnotes = []
names_not_caught = set()
speeches_per_day = {}
speakers_using_find = set()
speakers = set()
speaker_num_total_speeches = {}
speaker_num_total_chars = {}
speakers_per_session = {}
global speaker_list

def parseFiles(raw_speeches, multiple_speakers):
	# Assumes all xml files are stored in a Docs folder in the same directory as the python file
    files = os.listdir("AP_ARTFL_vols/")
    dates = set()
    num_sessions = 0
    num_morethan1_session = 0
    for filename in files:
        if filename.endswith(".xml"):
        	print(filename)
        	filename = open('AP_ARTFL_vols/' + filename, "r")
        	# Extracts volume number to keep track of for names_not_caught and speakers_using_find
        	volno = re.findall(vol_regex, str(filename))[0]
        	contents = filename.read()
        	soup = BeautifulSoup(contents, 'lxml')
        	pages = re.findall(page_regex, contents)
        	# Find all the sessions in the xml
        	sessions = soup.find_all(['div3'], {"type": ["other"]})
        	sessions_other = soup.find_all(['div2'], {"type": ["session"]})
        	sessions = sessions + sessions_other
        	# sessions = soup.find_all(['div2', 'div3'], {"type": ["session", "other"]})

        	for session in sessions:
		        date = extractDate(session)
		        # Restricts to valid dates we want to look at
		        if (date >= "1789-05-05") and (date <= "1795-01-04") and (date != "error"):
		        	# Datas is a dataset keeping track of dates already looked at
		        	# Accounts for multiple sessions per day
		        	num_sessions += 1
		        	if date in dates:
		        		num_morethan1_session += 1
		        		date = date + "_soir"
		        		if date in dates:
		        			date = date + "2"
		        			findSpeeches(raw_speeches, multiple_speakers, session, date, volno)
		        		else:
		        			findSpeeches(raw_speeches, multiple_speakers, session, date, volno)
		        			dates.add(date)		        		
		        	else:
		        		findSpeeches(raw_speeches, multiple_speakers, session, date, volno)
		        		dates.add(date)
	        filename.close()

def findSpeeches(raw_speeches, multiple_speakers, daily_soup, date, volno):
	id_base = date.replace("/","_")
	number_of_speeches = 0
	presidents = [">le President", "Le President", "Mle President", "President", "le' President", "Le Preesident", "Le Preseident", "Le Presidant", "Le Presideait", "le Presiden", "le President", "Le president", "le president", "Le President,", "Le Presideut", "Le Presidtent", "le Presient", "le Presldent", "le'President"]
	for talk in daily_soup.find_all('sp'):
		# Tries to extract the speaker name and edits it for easier pairing with the Excel file
		try:
			speaker = talk.find('speaker').get_text()
			speaker = remove_diacritic(speaker).decode('utf-8')
			speaker = speaker.replace("M.","").replace("MM ", "").replace("MM. ","").replace("M ", "").replace("de ","").replace("M. ","").replace("M, ","").replace("M- ","").replace("M; ","").replace("M* ","").replace(".","").replace(":","").replace("-", " ")
			if speaker.endswith(","):
				speaker = speaker[:-1]
			if speaker.endswith(", "):
				speaker = speaker[:-1]
			if speaker.startswith(' M. '):
				speaker = speaker[3:]
			if speaker.startswith(' '):
				speaker = speaker[1:]
			if speaker.endswith(' '):
				speaker = speaker[:-1]
		except AttributeError:
			speaker = ""

		speaker = speaker.lower()

		# Removes the footnotes
		speech_id = "" + id_base + "_" + str(number_of_speeches + 1)
		while talk.find("note"):
			ftnotes = talk.note.extract()
			ftnotes = remove_diacritic(ftnotes.get_text()).decode('utf-8')
			ftnotes = ftnotes.replace("\n","").replace("\r","").replace("\t","").replace("  "," ")
			footnotes.append([ftnotes, speaker, speech_id, volno])
		number_of_speeches += 1


# Parses dates from file being analyzed
def extractDate(soup_file):
	dates = soup_file.find_all('date')
	relevant_dates = []
	for date in dates:
		if date.attrs:
			relevant_dates.append(date)
	if (len(relevant_dates) > 0):
		return(relevant_dates[0]['value'])
	else:
		return("error")

if __name__ == '__main__':
	import sys
	speaker_list = load_speakerlist('Copy of AP_Speaker_Authority_List_Edited_3.xlsx')

	raw_speeches = {}
	multiple_speakers = {}
	parseFiles(raw_speeches, multiple_speakers)

	footnotes = pd.DataFrame(footnotes, columns = ["Footnote", "Speaker", "Speechid", "Volno"])

	write_to = pd.ExcelWriter("footnotes.xlsx")
	footnotes.to_excel(write_to, 'Sheet1')
	write_to.save()

       
   	
