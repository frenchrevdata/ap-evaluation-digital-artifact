# extract all i tags and sc tags and note tags
# look only at p tags

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
from parse_speaker_names import compute_speaker_Levenshtein_distance
import time


vol_regex = 'AP_ARTFL_vols\/AP(vol[0-9]{1,2}).xml'
page_regex = '<pb n="[\s0-9]+" facs="[\s\S]{0,300}" \/> [\s\S]{0,10000} <pb'


def parseEnc():
	# Assumes all xml files are stored in a Docs folder in the same directory as the python file
    files = os.listdir("Encyclopedie/")
    words = set()
    for filename in files:
        if filename.endswith(".tei"):
        	print(filename)
        	filename = open('Encyclopedie/' + filename, "r")
        	contents = filename.read()
        	soup = BeautifulSoup(contents, 'lxml')

        	paragraphs = soup.find_all('p')
        	for para in paragraphs:
        		if para.find("i"):
        			para.i.extract()
        		if para.find("sc"):
        			para.sc.extract()
        		if para.find("note"):
        			para.note.extract()
        		para = para.get_text()
        		para = para.replace("\n"," ").replace("& ","").replace("; ","").replace(".","").replace(",","").replace("?","").replace("!","").replace("  "," ")
        		paragraph = remove_diacritic(para).decode('utf-8')
        		para = para.lower()
        		paragraph = paragraph.split(" ")
        		words = words.union(paragraph)
    return words

def remove_stopwords(input, stopwords):
	filtered_text = ""
	for word in input.split():
		if word not in stopwords:
			filtered_text = filtered_text + " " + word
	return filtered_text

def checkErrors(enc_words, french_stopwords):
	files = os.listdir("AP_ARTFL_vols/")
	errors_per_vol = {}
	errors_per_page = {}
	word_freq_wrong = {}

	for filename in files:
	    if filename.endswith(".xml"):
	    	filename = open('AP_ARTFL_vols/' + filename, "r")
	    	volno = re.findall(vol_regex, str(filename))[0]
	    	print volno
	    	contents = filename.read()
	    	soup = BeautifulSoup(contents, 'lxml')

	    	num_errors = 0
	    	num_words_vol = 0
    		word_freq = {}

	    	# pages = re.findall(r'<pb n="[\s0-9]+" facs="[\s\S]{0,300}" \/> [\s\S]{0,10000} <pb', contents)
	    	# pages = re.findall(r'<pb n="[\s0-9]+" facs="[\s\S]{0,300}" \/> [\s\S]{0,8000} <pb', contents)
	    	# pages = re.findall(r'<pb n="[\s0-9]+" facs="[\s\S]{0,300}" \/>', contents)
	    	pb_tags = []
	    	last_index = 0
	    	while True:
	    		loc = contents.find("<pb n=", last_index)
	    		if loc == -1:
	    			break
	    		pb_tags.append(loc)
	    		last_index = loc + 1

	    	# Capture total number of words per vol and per page
	    	# Capture the words in a dictionary to also get frequency

	    	## SORT DICTIONARY WITHIN VOLUME

	    	# Create empty array, iterate through text and do contents.find for every <pb> tag while changing the substring
	    	for i in range(0, len(pb_tags)-1):
	    		contents_substr = contents[pb_tags[i]:pb_tags[i+1]]
	    		page_num = BeautifulSoup(contents_substr, 'lxml').find_all('pb')
	    		pb_soup = BeautifulSoup(contents_substr, 'lxml')
	    	# for i in range(0, len(pages)-1):
	    	# 	regex = pages[i] + '[\s\S]+' + pages[i+1]
	    	# 	page = re.findall(re.compile(regex), contents)[0]
	    		# page_num = BeautifulSoup(page, 'lxml').find_all('pb')
	    		pageno = volno + "_pg" + page_num[0].get("n")
	    		error_per_page = 0
	    		num_words_pg = 0

	    		text = unicode(contents_substr,"ascii", errors = "ignore")
	    		text = remove_diacritic(text).decode('utf-8')
    			paragraph = remove_stopwords(text, french_stopwords)
	    		# para = para.replace("s'","").replace("l'","").replace("d'","")
	    		paragraph = paragraph.replace("\n"," ").replace(")", "").replace("*","").replace(":","").replace("-","").replace("_","").replace("(","").replace("& ","").replace("; ","").replace(".","").replace(",","").replace("?","").replace("!","")
	    		paragraph = re.sub(r'([0-9]{1,4})', ' ', paragraph)
	    		words = paragraph.split(" ")
	    		num_words_vol += len(words)
	    		num_words_pg += len(words)
	    		for word in words:
	    			if word not in enc_words:
	    				if word in word_freq:
	    					word_freq[word] += 1
	    				else:
	    					word_freq[word] = 1
	    				error_per_page += 1
	    				num_errors += 1

		    	# paragraphs = pb_soup.find_all('p')


		    	# print("Before inner for loop = %f" % time.time())
		    	# for para in paragraphs:
		    	# 	while para.find("note"):
		    	# 		para.note.extract()
		    	# 	para = para.get_text().lower()
		    	# 	para = remove_diacritic(para).decode('utf-8')
		    	# 	para = para.replace("'", " ")
	    		# 	paragraph = remove_stopwords(para, french_stopwords)
		    	# 	# para = para.replace("s'","").replace("l'","").replace("d'","")
		    	# 	paragraph = paragraph.replace("\n"," ").replace(")", "").replace("*","").replace(":","").replace("-","").replace("_","").replace("(","").replace("& ","").replace("; ","").replace(".","").replace(",","").replace("?","").replace("!","")
		    	# 	paragraph = re.sub(r'([0-9]{1,4})', ' ', paragraph)
		    	# 	words = paragraph.split(" ")
		    	# 	for word in words:
		    	# 		if word not in enc_words:
		    	# 			error_per_page += 1
		    	# 			num_errors += 1
		    	# print("After inner for loop = %f" % time.time())
		    	errors_per_page[pageno] = [error_per_page, num_words_pg]

	    	# Iterate through all pairs of the page numbers found and use those to bound the regex (i.e. concatenate the two together
	    	# to form one regex. Have the characters in between the two regexs be enough)
	    	# Use the pg number from the first regex as the number for that page
	    	# for page in pages:
	    	# 	page_num = BeautifulSoup(page, 'lxml').find_all('pb')
	    	# 	pageno = volno + "_pg" + page_num[0].get("n")
	    	# 	error_per_page = 0
		    # 	paragraphs = soup.find_all('p')
		    # 	for para in paragraphs:
		    # 		if para.find("note"):
		    # 			para.note.extract()
		    # 		para = para.get_text().lower()
		    # 		para = remove_diacritic(para).decode('utf-8')
		    # 		para = para.replace("'", " ")
	    	# 		paragraph = remove_stopwords(para, french_stopwords)
		    # 		# para = para.replace("s'","").replace("l'","").replace("d'","")
		    # 		paragraph = paragraph.replace("\n"," ").replace(")", "").replace("*","").replace(":","").replace("-","").replace("_","").replace("(","").replace("& ","").replace("; ","").replace(".","").replace(",","").replace("?","").replace("!","")
		    # 		paragraph = re.sub(r'([0-9]{1,4})', ' ', paragraph)
		    # 		words = paragraph.split(" ")
		    # 		for word in words:
		    # 			if word not in enc_words:
		    # 				error_per_page += 1
		    # 				num_errors += 1
		    # 	errors_per_page[pageno] = error_per_page
		word_freq_wrong[volno] = word_freq
	   	errors_per_vol[volno] = [num_errors, num_words_vol]
	with open("errors_per_vol.pickle", 'wb') as handle:
		pickle.dump(errors_per_vol, handle, protocol = 0)
	w = csv.writer(open("errors_per_vol.csv", "w"))
	for key, val in errors_per_vol.items():
		if isinstance(key, str):
			key = unicode(key,"ascii", errors = "ignore")
		w.writerow([key,val[0],val[1]])

	with open("errors_per_page.pickle", 'wb') as handle:
		pickle.dump(errors_per_page, handle, protocol = 0)
	w = csv.writer(open("errors_per_page.csv", "w"))
	for key, val in errors_per_page.items():
		if isinstance(key, str):
			key = unicode(key,"ascii", errors = "ignore")
		w.writerow([key,val[0],val[1]])

	with open("word_freq_errors.pickle", 'wb') as handle:
		pickle.dump(word_freq_wrong, handle, protocol = 0)
	w = csv.writer(open("word_freq_errors.csv", "w"))
	for key, val in word_freq_wrong.items():
		w.writerow([key,val])


if __name__ == '__main__':
	import sys
	# words = parseEnc()
	# pickle_filename = "enc_words.pickle"
	# with open(pickle_filename, 'wb') as handle:
	# 	pickle.dump(words, handle, protocol = 0)
	enc_words = pickle.load(open("enc_words.pickle", "rb"))
	stopwords_from_file = open('FrenchStopwords.txt', 'r')
	lines = stopwords_from_file.readlines()
	french_stopwords = []
	for line in lines:
		word = line.split(',')
		#remove returns and new lines at the end of stop words so the parser catches matches
		#also remove accents so the entire analysis is done without accents
		word_to_append = remove_diacritic(unicode(word[0].replace("\n","").replace("\r",""), 'utf-8'))
		french_stopwords.append(word_to_append)
	checkErrors(enc_words, french_stopwords)
	# errors_per_vol = pickle.load(open("errors_per_vol.pickle", "rb"))
	# w = csv.writer(open("errors_per_vol.csv", "w"))
	# for key, val in errors_per_vol.items():
	# 	w.writerow([key,val])

