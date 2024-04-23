# Import libraries
# import imp
# Library for natural language processing tasks
import nltk
# Library for parsing HTML content
from bs4 import BeautifulSoup
# For cache invalidation
from importlib import invalidate_caches
# For JSON handling
import json
# For mathematical operations
import math
# For object serialization
import pickle
# Library for interacting with the operating system
import os
# Flask web framework
from flask import Flask
# Flask functions for rendering templates and handling requests
from flask import render_template, request, redirect
# Library for regular expressions (text processing)
import re


# Initialize Flask app
app = Flask(__name__)

# Define HTML file path
html_file_path = r'\Users\keerthanamucharla\Downloads\crawler\html_files'

# Define route for the homepage
@app.route("/")
def interface():
    """Renders the interface.html template, which displays the search bar."""
    return render_template('interface.html')

# Define route for getting the TF-IDF index
@app.route('/index', methods=['GET', 'POST'])

def getTF_IDF_Index():
  # Generate TF-IDF index
  invertedIndex = TF_IDFIndex(0)
  with open('invertedIndex.pk', 'wb') as pk_file:
    pickle.dump(invertedIndex,pk_file)
  pk_file.close()

  # Load the generated index from pickle file
  de_pickle = open('invertedIndex.pk', 'rb')

  content = pickle.load(de_pickle)

  json_invertedIndex = json.dumps(content)
  return render_template('invertedIndex.html', inverted_index=json_invertedIndex)

# Define route for search functionality
@app.route('/search', methods=['GET', 'POST'])

def search():
  
  form = request.form
  query = str(form['query'])
  # Generate TF-IDF index for search
  invertedIndex = TF_IDFIndex(1)
  errors = QueryErrors(query, invertedIndex)

  if len(errors) == 0:
    
    legend = fileLegend()
    queryVector = QueryVector(query)
    scores = CSSearch(queryVector)
    return render_template('cssearch.html', legend=legend, queryVector=queryVector, scores=scores)

  corrections = []
  for error in errors:
    corrections.append((error, SpellingCorr(error,invertedIndex)))

  return render_template('interface.html', corrections=corrections)

# Function to calculate Term Frequency (TF)
def TermFrequency(term, file):

  wordCount = 0 
  termCount = 0       

  for word in file:
    if word == term:      
      termCount += 1
    wordCount += 1
  return (termCount/wordCount)

def InverseDF(term, corpus_count, index):
  """Calculates IDF for a term based on the number of documents it appears in."""
  df = len(index[term])  
  return math.log10(corpus_count/(df + 1))  

# Function to generate file legend
def fileLegend():

  filenames ={}
  docID = 0
  for file in os.listdir(html_file_path):     
    docID+=1
    file = file.replace(" ", "_")
    filenames[docID] = (f'https://en.wikipedia.org/wiki/{file[:-5]}')
  return filenames

# Function to generate TF-IDF index
def TF_IDFIndex(valueType):  

  # Initialize inverted index and corpus
  invertedIndex = {} 
  corpus = {} 
  docID = 0

  filenames = fileLegend()  
  # Iterate through HTML files
  for file in os.listdir(html_file_path):    
    docID+=1
    with open(os.path.join(html_file_path, file), encoding="utf8") as html_file:     
      soup = BeautifulSoup(html_file.read(), 'lxml')     
      processedTxt = []     
      for tag in soup.find_all('p'):      
        processedTxt.extend((re.sub('[^A-Za-z0-9]+',' ',' '.join(tag.text.split())).split()))
        
      for tag in soup.find_all('dd'):
          processedTxt.extend((re.sub('[^A-Za-z0-9]+',' ',' '.join(tag.text.split())).split()))
      corpus[file] = processedTxt
      html_file.close()

      for word in processedTxt:
         if word in invertedIndex and docID not in invertedIndex[word]:
           invertedIndex[word].append(docID)
         else:
           invertedIndex[word] = [docID]

  # Calculate TF-IDF scores
  for key in invertedIndex.keys():       
        docIDLst = invertedIndex[key]       
        idf_score = InverseDF(key, len(os.listdir(html_file_path)), invertedIndex)        
        invertedIndex[key] = []        
        for docID in docIDLst:          
          tf_score = TermFrequency(key,corpus[file])
          if valueType != 1:           
            invertedIndex[key].append((filenames[docID],(tf_score*idf_score)))
          else:
            invertedIndex[key].append((docID,(tf_score*idf_score)))
  return invertedIndex 

# Function to generate query vector
def QueryVector(query, tf_idf_index = TF_IDFIndex(1)):

  qvDict = {}           
  tokenizedQuery = list(query.split(" "))

  for token in tokenizedQuery:
    if token not in tf_idf_index:
      qvDict[token] = 0
      continue
    qvDict[token] = InverseDF(token, len(os.listdir(html_file_path)), tf_idf_index)
  return qvDict

# Function to calculate document length
def DocLength(queryVector, docID, tf_idf_index):

  sum = 0
  for term in queryVector:
    if docID not in tf_idf_index[term]:
      continue
    for pair in tf_idf_index[term]:
      if pair[0] == docID:
        sum += pair[1] ** 2
        break 
  return math.sqrt(sum)

# Function for cosine similarity search
def CSSearch(queryVector, tf_idf_index = TF_IDFIndex(1)):  

  scores = [(0,0)] * len(os.listdir(html_file_path))
  for term, idf in queryVector.items():
    for (docID, tf_idf) in tf_idf_index[term]:
      if (docID - 1) in scores:
        scores[docID - 1][1] += idf*tf_idf
        continue
      scores[docID - 1] = (docID, (idf*tf_idf))
  scores = sorted(list(set([score for score in scores])))
  for score in scores:
    docLength = DocLength(queryVector, score[0], tf_idf_index)
    if docLength == 0:
      continue
    score[1] = score[1]/docLength 

  return scores

# Function to identify query errors
def QueryErrors(query, index):
  
  errors = []
  splitQuery = query.split()

  for term in splitQuery:   
    if term not in index.keys():     
      errors.append(term)

  return errors  

# Function for spelling correction
def SpellingCorr(query,index):        #              

  bigramDict = {}          
  bigrams = []
  nwcQuery = query        
  query = "$" + query + "$" 

  for x in range (1,len(query)):
      bigramDict[(query[x-1:x+1]).replace("$","")] = []     
      bigrams.append(query[x-1:x+1]) 
  
  for bigram in bigrams:

    if "$" in bigram[0]:                                   
      for key in index.keys():                             
        if bigram[1] == key[0]:
          bigramDict[bigram[1]].append(key)

    elif "$" in bigram[1]:                                  
      for key in index.keys():
        if bigram[0] == key[-1]:
          bigramDict[bigram[0]].append(key)

    else:
      for key in index.keys():                              
        if bigram in key:                 
          bigramDict[bigram].append(key)

  bigrams.clear()
  
  for x in range (1,len(query)):                            
    bigrams.append((query[x-1:x+1]).replace("$",""))

       

  editDists = []                   
  minDists = []                     

  for bigram in bigrams:
    editDist = []                   
    for term in bigramDict[bigram]:
      editDist.append(nltk.edit_distance(nwcQuery,term))
    editDists.append(editDist)

  for lst in editDists:
    if len(lst) == 0:
      continue
    minDists.append(min(lst))



  minDist = min(minDists)
  suggestions = []           

  pointer = -1                
 
  for lst in editDists:
    pointer+=1
    for x in range(0,len(lst)):
      if lst[x] == minDist:
        suggestions.append(bigramDict[bigrams[pointer]][x])

  return list(set(suggestions))        
    

if __name__ == '__main__':
  app.run(debug=True)
