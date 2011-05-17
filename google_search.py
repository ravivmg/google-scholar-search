import httplib
import urllib
from BeautifulSoup import BeautifulSoup
import re
import time

class GoogleScholarSearch:
    def __init__(self):
        self.SEARCH_HOST = "scholar.google.com"
        self.SEARCH_BASE_URL = "/scholar"

    def search(self, terms, limit=10):
        start = 0
        results = []
        while start+10<=limit:
            params = urllib.urlencode({'q': "+".join(terms),'as_yhi': 2008, 'start': start })
            headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

            url = self.SEARCH_BASE_URL+"?"+params
            conn = httplib.HTTPConnection(self.SEARCH_HOST)
            conn.request("GET", url, {}, headers)
    
            resp = conn.getresponse()      
            if resp.status==200:
                html = resp.read()
                html = html.decode('ascii', 'ignore')
                        
                # Screen-scrape the result to obtain the publication information
                soup = BeautifulSoup(html)
                citations = 0
                for record in soup('div', {'class': 'gs_r'}):
             
                    # Includeds error checking
                    topPart = record.first('h3')                                
                        
                    pubURL = topPart.a['href']
                
                    # Clean up the URL, make sure it does not contain '\' but '/' instead
                    pubURL = pubURL.replace('\\', '/')

                    pubTitle = ""
                    for part in topPart.a.contents:
                        pubTitle += str(part.string)
                

                    if pubTitle == "":
                        match1 = re.findall('<b>\[CITATION\]<\/b><\/font>(.*)- <a',str(record))
                        match2 = re.split('- <a',match1[citations])
                        pubTitle = re.sub('<\/?(\S)+>',"",match2[0])
                        citations = citations + 1
               
                    authorPart = record.first('span', {'class': 'gs_a'}).string
                    if authorPart == None:
                        authorPart = re.search('<span class="gs_a">(.*?)</span>',str(record)).group(1)
                    num = authorPart.count(" - ")
                    # Assume that the fields are delimited by ' - ', the first entry will be the
                    # list of authors, the last entry is the journal URL, anything in between
                    # should be the journal year
                    idx_start = authorPart.find(' - ')
                    idx_end = authorPart.rfind(' - ')
                    pubAuthors = authorPart[:idx_start]             
                    pubJournalYear = re.search('\d{4}',authorPart[idx_start + 3:idx_end]).group(0)
                    pubJournalURL = authorPart[idx_end + 3:]
                    # If (only one ' - ' is found) and (the end bit contains '\d\d\d\d')
                    # then the last bit is journal year instead of journal URL
                    if pubJournalYear=='' and re.search('\d\d\d\d', pubJournalURL)!=None:
                        pubJournalYear = pubJournalURL
                        pubJournalURL = ''
                               
                    # This can potentially fail if all of the abstract can be contained in the space
                    # provided such that no '...' is found
                    delimiter = soup.firstText("...").parent
                    pubAbstract = ""
                    while str(delimiter)!='Null' and (str(delimiter)!='<b>...</b>' or pubAbstract==""):
                        pubAbstract += str(delimiter)
                        delimiter = delimiter.nextSibling
                    pubAbstract += '<b>...</b>'
                
                    match = re.search("Cited by ([^<]*)", str(record))
                    pubCitation = ''
                    if match != None:
                        pubCitation = match.group(1)
                    results.append({
                        "URL": pubURL,
                        "Title": pubTitle,
                        "Authors": pubAuthors,
                        "JournalYear": pubJournalYear,
                        "JournalURL": pubJournalURL,
                        "Abstract": pubAbstract,
                        "NumCited": pubCitation,
                        "Terms": terms
                    })
            else:
                print "ERROR: ",
                print resp.status, resp.reason
                return []
            start+=10
            time.sleep(3)
        return results

if __name__ == '__main__':
    search = GoogleScholarSearch()
    pubs = search.search(["breast cancer", "gene"], 20)
    fout = open('','w+')
    for pub in pubs:
        firstauthortxt = pub['Authors'].split(', ')[0]
        firstauthor = firstauthortxt.split(' ')[1]+", "+firstauthortxt.split(' ')[0]
        print pub['Title']
        print pub['Authors']
        print pub['JournalYear']
        print pub['Terms']
        fout.write(firstauthor+'\t'+pub['JournalYear']+'\t'+pub['Title']+'\n')
        print "======================================"
    fout.close()