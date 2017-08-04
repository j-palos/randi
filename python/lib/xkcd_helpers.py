import urllib.error
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import bs4.element
import json

EXPLAIN_URL = "http://www.explainxkcd.com/wiki/index.php"

INC_STR = "This transcript is incomplete. Please help editing it! Thanks."


#==============================================================================#
#==============================================================================#

# Say that a file couldn't be reached
def fileNotFound (prompt, f):
    print (prompt + " An error ocured while retrieving data from " + f + \
            "\nMake sure the files exists and is accessible.")

#==============================================================================#
#==============================================================================#

# e,g t = '23: This is the title - explain xkcd'
# This will remove the trailing ' - explain xkcd'
# And '23: '
# And return the resulting string 'This is the title'
def extractTitle (t):
    title = t.split (' - explain xkcd')
    title = title [0]
    # Remove every char from the beginning until a whitespace is found
    while title [0] != ' ':
        title = title [1:]
    # Return the string minus the first char which is a whitespace
    return title [1:]

#==============================================================================#
#==============================================================================#

# Fetches a webpage
# Returns the content of the css elements 'dl' and the xpath '//img@/alt
# Return codes:
#  0 -> success; 
# -1 -> requested elements not found; 
# -2 -> error with the browser
def fetch (bruh, url):
    transcript, alt, title = None, None, None
    try:
        bruh.visit (url)
        transcript = bruh.find_by_css ('dl').value
        # This might fail with 'phantomjs'
        alt = bruh.find_by_xpath ('//img/@alt').value
        title = extractTitle (bruh.find_by_css ('title').value)
        link = bruh.find_by_xpath ('//img/@src').value
        return [0, title, alt, transcript, link]
    except:
        # why am I writing pseudocode
        if (transcript is None or alt is None or title is None):
            return list [-1]
        # what could go wrong
        else:
            return list [-2]

#==============================================================================#
#==============================================================================#

# Returns the arguments in reversed order
def switchValues (a, b):
    return b, a

#==============================================================================#
#==============================================================================#

# Returns the two first elements of the list, sorted
# Return codes:
#  0 -> Success; 
# -1 -> Insufficient arguments; 
# -2 -> Invalid arguments
def getArgs (args):
    if (len(args) == 1):
        try:
            first = abs ( int (args [0]))
            last = first
        except:
            return [-2]
    elif (len(args) >= 2):
        try:
            first = abs (int (args [0]))
            last = abs (int (args [1]))
        except:
            return [-2]
    else:
        return [-1]

    if (first > last):
        first, last = switchValues(first, last)

    return [0, first, last]

#==============================================================================#
#==============================================================================#

# Remove any  non alpha characters in a string
# Doesn't remoe ' ' nor '-' if surrounded by alpha chars
# p is as string
# phrase (return value) is a string
def removePunk (p):
    p = p.replace('\n', ' ')
    phrase = str ()
    for i in range (len (p)):
        if p[i].isalpha () or p[i].isdigit ():
            phrase += p[i]
        elif p[i] == ' ':
            if i - 1 > 0 and i + 1 < len (p):
                if p[i - 1].isalpha ():
                    phrase += p[i]
                else:
                   phrase += ' '
            else:
                phrase += ' '
        elif p[i] == '-':
            if i - 1 > 0 and i + 1 < len (p):
                if p[i - 1].isalpha () and p[i + 1].isalpha ():
                    phrase += p[i]
                else:
                    phrase += ' '
            else:
                phrase += ' '
        else:
            phrase += ' '

    return phrase.lower ()

#==============================================================================#
#==============================================================================#
# Remove everyword in wl which is also in bl
# wl is a list
# bl is alist
def removeBlack (wl, bl):
    for b in bl:
        if b in wl:
            wl.remove (b)

#==============================================================================#
#==============================================================================#

# Add or update the representation of a word in the index
# word is string`
# comic_number is an int
# index is a dictionary
# index => {word : {comic_number: value}}
# if the word is in the index:
#   if comic_number is in the word (word in the index is dict too):
#       value for comic_number is increased
#   else: comic_number is added to word with value 1
# else: word is added to index with value {comic_number: 1}
def indexWord (word, comic_number, index):
    if word in index:
        if comic_number in index [word]:
            index [word][comic_number] += 1
        else:
            index [word][comic_number] = 1
    else:
        index [word] = dict (zip ([comic_number], [1]))

#==============================================================================#
#==============================================================================#

# Call indexWord on each string in phrase
# phrase is a list of strings
# comic_number is an int
# index is a dict
def indexPhrase (phrase, comic_number, index):
    for word in phrase:
        indexWord (word, comic_number, index)

#==============================================================================#
#==============================================================================#

# Transform a string in list of unique words
# Remove any word appearing in the blcklist from the list
# Call indexPhrase on the reulting list
# comic is a string
# comic_number is an int
# index is dict
# black_list is a list
def indexComic (comic, comic_number, index, black_list):
    phrase = comic.split (' ')
    
    # Magic happens here: 
    # remove empty string, whitespaces and stop words from the list
    phrase = [ x for x in phrase if x and not (x == ' ' or x in black_list) ]
       
    #removeBlack (phrase, black_list)
    indexPhrase (phrase, comic_number, index)

#==============================================================================#
#==============================================================================#

# Remove words inside brackets, aka noise
# In "haha lo [l kek x] D lmao"
# It'll remoe "[l kek x]"
# And return "haha lol  D lmao"
def removeNoise (s):
    import re
    regex = re.compile (".*?\[(.*?)\]")
    clean = re.sub (regex, "", s)
    return clean

#==============================================================================#
#==============================================================================#

# Get the html for a comic from the explainxkcd website
# Extract the transcript from the text
# Check if the transcript is mark as incomplete
#   if yes, mark it as so locally (for later updates)
# Returns a dictionary (result)
# If an error occured the status is not 0 and the error is passed in the error
# field of the returned dictionary

def get_transcript (number=''):
    result = {'status': 0, 'error': '', 'num': number, 'tr': '', 'complete': 0}
    request = Request('{}/{}'.format(EXPLAIN_URL, number),\
            headers={'User-Agent': 'Mozilla/5.0'})
    try:
        # Get page and create xml tree
        raw = urlopen(request).read ()
        soup = BeautifulSoup (raw, 'html.parser')
        #return soup
        # Check if the transcript is complete
        result['complete'] = transcript_is_complete(soup)
        
        # Retrieve transcript
        tr_i = soup.select("#Transcript")[0].find_next()
        done = False
        transcript = []
        while not done:
            if type(tr_i) is bs4.element.NavigableString:
                transcript.append(tr_i)
            elif type(tr_i) is bs4.element.Comment:
                pass
            else:
                transcript.append(tr_i.text)
                
            tr_i = tr_i.next_sibling
            
            if tr_i.name == 'h2' or tr_i.name == 'span':
                done = True
        
        transcript = ' '.join(transcript)
        transcript = ' '.join(transcript.split(INC_STR)) 
        result['tr'] = transcript
        return result
    except urllib.error.HTTPError as uehe: # shrug
        result['status'] = -1
        result['error'] = uehe
        return result
    except IndexError as ie: # If there is no #Transript id on the page
        result['status'] = -2
        result['error'] = ie
        return result

#==============================================================================##==============================================================================#
# Check if a transcript is marked as incomplete
# if yes: returns 1
# else returns 0
# if transcript isn't present at all, returns 2
def transcript_is_complete(soup):
    try:
        transcript = soup.select("#Transcript")[0]
        next_tag = transcript.find_next ()
        if next_tag.name == 'table':
            if len(next_tag.text.split(INC_STR)) > 0:
                return -1
    
        return 0
    except IndexError as ie: # Comic has no transcript
        return -2
    except:
        return -3

#==============================================================================#
#==============================================================================#

# Duplicated from lib/client
def get_xkcd(number = 0):
    if number is 0:
        url ='https://xkcd.com/info.0.json'
    else:
        url = 'https://xkcd.com/{}/info.0.json'.format (number)

    response = {'status': 0, 'error': '', 'comic': ""}

    try:
        online_comic = urlopen(url).read ()
        response['comic'] = json.loads (online_comic.decode('utf-8'))
    except urllib.error.HTTPError:
        response['status'] = -1
    except:
        response['status'] = -2

    return response

#==============================================================================##==============================================================================#
