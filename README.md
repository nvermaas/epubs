
pip install pypdf
pip install EbookLib
pip install requests
pip install beautifulsoup4

### scrape all the pdfs from the NASA Oral History website
python epubs.py --parfile configs\collect_pdfs.arg

### try to find the astronauts in that heap of 1200 pdf's 
python epubs.py --parfile configs\find_astronauts.arg

