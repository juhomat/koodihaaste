# -*- coding: utf-8 -*-

import requests
import json
import os
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from fuzzywuzzy import fuzz

def caesar_cipher(string, key):
    
    cipher = ""
    
    # I build the cipher individually for each words. 
    # I was hoping that there would be an eastern egg where a different key would have been used for each word in the same sentence. 
    # Originally I checked if the word was Finnish right after the cipher. But there was no easter egg or I couldn't find it :)
    # So I changed the structure that the Finnish check is done for the whole sentence and in a separate function. I still left this in a way that each word is a separate cipher.
    
    split = string.split(' ')
    
    for word in split:
        
        for char in word:
            
            order = alphabets.find(char)
            
            # only cipher alphabetical characters
            if(order >= 0):
                
                char_key = order + key
                
                # go back to start of the alphabets if key goes over 29
                if(char_key >= 29):
                    char_key = char_key - 29
                
                cipher_char = alphabets[char_key]
                
                cipher = cipher + cipher_char
            
            else:
                cipher = cipher + char
        
        cipher = cipher + " "
    
    return cipher.rstrip()

    
def check_finnish(phrase):
    
    words = phrase.split(' ')
    
    phrase_total_words = len(words)
    phrase_finnish_words = 0
    
    for word in words:
        
        is_finnish = check_word_finnish(word)
        
        if is_finnish == 1:
            phrase_finnish_words = phrase_finnish_words + 1
            
    return (phrase_finnish_words / phrase_total_words)
        
def check_finnish_fuzzy(phrase):
    
    total_correlation = 0.0
    hundred_count = 0
    
    words = phrase.split(' ')
    
    word_count = len(words)
    
    for word in words:
        
        # only check words with at least 3 characters, short words in inflected fors give poor matches even though they are Finnish (e.g. 'on' which is past form of word 'olla' but gives a poor fuzzy score)
        if(len(word) < 3):
            word_count = word_count - 1
            continue
    
        max_correlation = 0.0

        # This is quite slow since all the +90000 are compared. It could be made faster to only include words which start with the same letter etc.. 
        for finnish_word in finnish_words:

            correlation = fuzz.ratio(word.lower(),finnish_word.lower())
            if(correlation > max_correlation):
                max_correlation = correlation

            if(correlation == 100):
                hundred_count = hundred_count + 1
                break
        
        total_correlation = total_correlation + max_correlation
        
    # return average with and withouth the exact word matches
    score = {'without_hundred': (total_correlation - (hundred_count * 100)) / (word_count - hundred_count), 'total' : (total_correlation / (word_count))}
    
    return score
    

def check_word_finnish(word):
    
    if word in finnish_words:
        return 1
    
    # Remove last character to check if the word is in inflected form. 
    # This of course doesn't find all the words but it does good enough job to define if the sentence could be Finnish. Fuzzy logic will then do more calculations.
    
    word = word[:-1]
    while len(word) > 2:
        
        if word in finnish_words:
            return 1
        else:
            word = word[:-1]
        
    return 0
    

# define alphabets
alphabets = 'abcdefghijklmnopqrstuvwxyzåäö'

# define finnish words
finnish_words = []

# Get Finnish words from Kotimaisten kielten keskus (http://kaino.kotus.fi/sanat/nykysuomi/)
url = 'http://kaino.kotus.fi/sanat/nykysuomi/kotus-sanalista-v1.zip'
urllib.request.urlretrieve(url, 'wordlist_xml.zip')

# unzip and read
with zipfile.ZipFile('wordlist_xml.zip', 'r') as zip_ref:
    zip_ref.extractall('')

#parse words
root = ET.parse('kotus-sanalista_v1/kotus-sanalista_v1.xml').getroot()

for st in root.findall('st'):
    for s in st:
        if (s.tag == 's'):
            finnish_words.append(s.text)
            
# remove files
shutil.rmtree('kotus-sanalista_v1')
os.remove('wordlist_xml.zip')


# get challenge data from API
response = requests.get('https://koodihaaste-api.solidabis.com/secret')
res = response.json()
token = res['jwtToken']

data = requests.get(
    'https://koodihaaste-api.solidabis.com/bullshit',
    headers={'Authorization': token}
)

dataDict = data.json()
bullshits = dataDict['bullshits']

# check each message whether bullshit or not
no_bull = []
bull = []

count = 0

for bullshit in bullshits:

    # Count three scores. Finnish score is matching word to finnish word database with a simple string comparison
    # Fuzzy score is same with fuzzy logic and average on the score of each word.
    # Fuzzy score without hundred is the same except that exact matches are not counted to the average. This way the phrases that contain a lot of Finnish words but also total bullshit words can be found.
    finnish_score = 0.0
    fuzzy_score = 0.0
    fuzzy_score_without_hundred = 0.0
    
    i = 0
    
    # loop through keys and stop if Finnish is found
    while (i < len(alphabets)):
        
        # cipher without the last dot and with lower case
        phrase = caesar_cipher(bullshit['message'][:-1].lower(), i)
        
        # check if finnish with a sting comparison against word database
        finnish_score = check_finnish(phrase)
        
        # With the string comparison (the variable finnish_score) the most pharses can be weed out so fuzzy score (which is quite slow) can be calculated only with the ones that match at least some finnish words.
        # However in a cloud environment where computing is a not an issue this could always be calculated
        if (finnish_score > 0.4 ):
            fuzzy_score_dict = check_finnish_fuzzy(phrase)
            fuzzy_score = fuzzy_score_dict['total']
            fuzzy_score_without_hundred = fuzzy_score_dict['without_hundred']

        # check the scores if phrase is Finnish. The needed scores are based in my own analysis of the results. So the original data is used as a training data set.
        if(finnish_score > 0.47 and fuzzy_score > 82.2 and fuzzy_score_without_hundred > 80.1):
            no_bull.append(phrase.capitalize() + ".")
            
            # If you want to follow along the progress you can uncomment the print
            print ("No Bull: " + str(count+1) + ". " + phrase.capitalize() + ".")
            break
        
        i = i + 1
        
        if(i == len(alphabets)):
            bull.append(bullshit['message'])
            
            # If you want to follow along the progress you can uncomment the print
            print ("Bull: " + str(count+1) + ". " + bullshit['message'])
        
    count = count + 1

print ("No Bull:")    
for x in no_bull:
    print (x)
    
print ("Bull:")
for x in bull:
    print (x)
