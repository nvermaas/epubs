import os,sys,shutil
import argparse
import pypdf
import requests
from bs4 import BeautifulSoup

from ebooklib import epub

class MyPDF:
    def __init__(self, filepath, args):
        self.reader = pypdf.PdfReader(filepath)
        self.args = args

    def extract_text(self):
        chapter_text = ""

        count = 0
        for page in self.reader.pages:

            count += 1

            # extracting text from page
            page_text = page.extract_text()

            # replace \n with <br>
            if args.lf_to_br:
                page_text = page_text.replace('\n', '<br>')

            # remove the header of every original pdf page
            if args.cut_page_header:
                if count > 1:
                    page_text = page_text.split('<br>', 1)[1]

            # remove the footer and paging of the original pdf (everything after the last <br>)
            if args.cut_page_footer:
                page_text = page_text.rsplit('<br>', 1)[0]

            chapter_text = chapter_text + page_text

        #print(chapter_text)
        return chapter_text

class MyHTM:
    def __init__(self, filepath, args):
        self.filepath = filepath
        self.args = args

    def extract_text(self):

        with open(self.filepath, 'r') as file:
            # Read the entire file content into a string
            file_content = file.read()

        return file_content


class MyBook:
    def __init__(self, args):
        self.book = epub.EpubBook()
        self.book.set_title(args.title)
        self.book.set_language("en")
        self.book.add_author(args.author)

        # create image from the local image
        image_content = open(args.cover_image, "rb").read()
        self.book.set_cover("cover_image.jpg", image_content)

        cover = epub.EpubHtml(title=args.title, file_name="chapter_0.xhtml" , lang="en")
        cover.content = (
                "<p><img src='cover_image.jpg' width='1000px' alt='Cover Image'/></p>"
        )
        self.book.add_item(cover)

        self.spine = [cover,'nav']
        self.toc = []

    def add_chapter(self, title, chapter_text, chapter_image=None):

        # create chapter
        count = len(self.spine)-1
        filename = f"chapter_{count}.xhtml"

        c = epub.EpubHtml(title=title, file_name=filename, lang="en")
        if chapter_image:
            image_content = open(chapter_image, 'rb').read()

            filename_in_epub = os.path.split(chapter_image)[1]
            img = epub.EpubImage(uid=filename_in_epub.lower(), file_name=filename_in_epub.lower(), content=image_content)
            #img = epub.EpubImage(uid=chapter_image.lower(), file_name=chapter_image.lower(), content=image_content)
            self.book.add_item(img)

            c.content = (
                    "<p><img src='" + filename_in_epub.lower()+"' width='1000px' alt='Cover Image'/></p>"
                    "<h2>" + title + "</h2>"
                    "<p>" + chapter_text + "</p>"
            )
        else:
            c.content = (

                    "<h2>" + title + "</h2>"
                    "<p>" + chapter_text + "</p>"
            )
        self.book.add_item(c)
        self.spine.append(c)

        # keep table of contents
        toc_object = epub.Link(filename,title,title)
        self.toc.append(toc_object)

    def save(self, args):
        # generate Table Of Contents
        self.book.toc = tuple(self.toc)

        # add default NCX and Nav file
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # define CSS style
        if args.css!=None:
            with open(args.css, 'r') as file:
                # Read the entire file content into a string
                style = file.read()
        else:
            style = "BODY {color: white;}"

        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="mystyle.css",
            media_type="text/css",
            content=style,
        )

        # add CSS file
        self.book.add_item(nav_css)

        # basic spine
        self.book.spine = self.spine

        # write to the file
        epub.write_epub(args.output, self.book, {})


#========================================================================
def single_pdf_to_epub(args):

    print(f'converting {args.input}...')
    # open the pdf and extract the text
    myPDF = MyPDF(args.input,args)
    chapter_text = myPDF.extract_text()

    # create the epub
    myBook = MyBook(args)

    # add the extracted text from the pdf as a chapter
    filename = os.path.basename(args.input)
    subtitle = os.path.splitext(filename)[0]
    myBook.add_chapter(subtitle, chapter_text)

    # save the epub file
    myBook.save(args)
    print(f'saved as {args.output}')


def directory_with_pdf_to_epub(args):

    # create the epub
    myBook = MyBook(args)

    # Iterate over all files in the directory
    for filename in os.listdir(args.input_directory):
        filepath = os.path.join(args.input_directory, filename)

        extention = os.path.splitext(filename)[1]

        # open the pdf and extract the text
        if extention == '.pdf':
            if args.filter.upper() in filename.upper():
                print(f'converting {filepath}...')
                myPDF = MyPDF(filepath, args)
                chapter_text = myPDF.extract_text()

                subtitle = os.path.splitext(filename)[0]
                myBook.add_chapter(subtitle, chapter_text)

    # save the epub file
    myBook.save(args)
    print(f'saved as {args.output}')


def directory_with_html_to_epub(args):

    # create the epub
    myBook = MyBook(args)

    # Iterate over all files in the directory
    for filename in os.listdir(args.input_directory):
        filepath = os.path.join(args.input_directory, filename)

        extention = os.path.splitext(filename)[1]

        # open the pdf and extract the text
        if extention == '.htm':
            if args.filter.upper() in filename.upper():
                print(f'converting {filepath}...')
                myHTM = MyHTM(filepath, args)
                chapter_text = myHTM.extract_text()
                subtitle = os.path.splitext(filename)[0]

                # if a jpg exists with the same basename as the htm, then add it as chapter image
                chapter_image = os.path.splitext(filepath)[0] + '.jpg'
                if os.path.exists(chapter_image):
                    myBook.add_chapter(subtitle, chapter_text, chapter_image)
                else:
                    myBook.add_chapter(subtitle, chapter_text)

    # save the epub file
    myBook.save(args)
    print(f'saved as {args.output}')

def directory_with_pdf_to_txt(args):

    # create the textfile
    with open(args.output, 'w') as f:

        # Iterate over all files in the directory
        for filename in os.listdir(args.input_directory):
            filepath = os.path.join(args.input_directory, filename)

            extention = os.path.splitext(filename)[1]

            # open the pdf and extract the text
            if extention == '.pdf':
                if args.filter.upper() in filename.upper():
                    print(f'converting {filepath}...')
                    myPDF = MyPDF(filepath, args)
                    subtitle = os.path.splitext(filename)[0]
                    chapter_text = myPDF.extract_text()

                    f.write(subtitle)
                    f.write('\n')
                    f.write(chapter_text)

    print(f'saved as {args.output}')

def collect_pdfs(args):
    base_url = args.pdf_host.rsplit('/', 1)[0]

    response = requests.get(args.pdf_host)
    base_soup = BeautifulSoup(response.content, 'html.parser')

    a_elements  = base_soup.find_all('a', href=True)

    # skip the first 27
    a_elements = a_elements[55:]

    for a in a_elements:
        url = a['href']

        if not 'http' in url:
            # this is potentially a page containing pdf's
            url = base_url + '/' + url
            print(url)

            response = requests.get(url)

            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links on the page
            links = soup.find_all('a', href=True)

            # Filter links to find PDF files
            pdf_links = [link['href'] for link in links if link['href'].endswith('.pdf')]

            # Download each PDF file
            for pdf_link in pdf_links:
                try:
                    if pdf_link.startswith('http'):
                        continue
                    else:
                        # cut off the .htm file
                        pdf_url = url.rsplit('/', 1)[0] + '/'+ pdf_link

                    filename = os.path.join(args.output, os.path.basename(pdf_url))

                    # check if this pdf already exists, then skip it.
                    if not os.path.exists(filename):

                        # Download the PDF
                        pdf_response = requests.get(pdf_url)
                        if pdf_response.status_code == 200:
                            with open(filename, 'wb') as f:
                                f.write(pdf_response.content)
                                print(f"Downloaded: {filename}")
                except:
                    # only convert what works, skip the rest
                    pass

def find_astronauts(args):
    # scan the input directory for _Bio files
    files = os.listdir(args.input)

    # gather all the biographies
    astronauts = []
    for filename in files:

        if '_BIO' in filename.upper():
            # who is this?
            prefix = filename.rsplit('_',1)[0]

            # go look in the pdf for missions
            source = os.path.join(args.input, filename)
            myPDF = MyPDF(source, args)

            print(f'checking {filename} for missions...')

            contents = myPDF.extract_text()
            if "MISSIONS :" in contents.upper() or "ASTRONAUT " in contents.upper() or "MISSIONS:" in contents.upper():
                print(f'{prefix} is an astronaut! :-)')
                astronauts.append(prefix)


    # Iterate over the bio's
    for astronaut in astronauts:
        for filename in files:
            if astronaut.upper()+'_' in filename.upper():
                source = os.path.join(args.input, filename)
                target = os.path.join(args.output,filename)
                shutil.move(source,target)


def get_arguments(parser):
    """
    Gets the arguments with which this application is called and returns
    the parsed arguments.
    If a parfile is give as argument, the arguments will be overrided
    The args.parfile need to be an absolute path!
    :param parser: the argument parser.
    :return: Returns the arguments.
    """
    args = parser.parse_args()
    if args.parfile:
        args_file = args.parfile
        if os.path.exists(args_file):
            parse_args_params = ['@' + args_file]
            # First add argument file
            # Now add command-line arguments to allow override of settings from file.
            for arg in sys.argv[1:]:  # Ignore first argument, since it is the path to the python script itself
                parse_args_params.append(arg)

            args = parser.parse_args(parse_args_params)
        else:
            raise (Exception("Can not find parameter file " + args_file))
    return args

def parse_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

    parser.add_argument("--version",
                        default=False,
                        help="Show current version of this program.",
                        action="store_true")

    parser.add_argument("--input", "-i",
                        default=None,
                        help="input pdf file or directory to convert to epub",
                        )
    parser.add_argument("--input_directory",
                        default=None,
                        help="directory that contains the pdf's to convert to epub",
                        )
    parser.add_argument("--output", "-o",
                        default=None,
                        help="output epub file",
                        )
    parser.add_argument("--title",
                        default="",
                        help="Title of the book",
                        )
    parser.add_argument("--subtitle",
                        default="",
                        help="Subtitle of the book",
                        )
    parser.add_argument("--author",
                        default="Nico Vermaas",
                        help="author",
                        )
    parser.add_argument("--css",
                        default=None,
                        help="path to a css file that can be applied in the epub (optional)",
                        )
    parser.add_argument("--cover_image",
                        default=None,
                        help="Cover image of the epub",
                        )
    parser.add_argument("--filter",
                        default="",
                        help="All pdf's with this substring in the name will be read",
                        )
    parser.add_argument("--conversion",
                        default="pdf_to_epub",
                        help="pdf_to_epub, pdf_to_txt, txt_to_epub, html_to_epub",
                        )
    parser.add_argument("--lf_to_br",
                        default=False,
                        help="Converts '\\n' to <br> ",
                        action="store_true")
    parser.add_argument("--cut_page_header",
                        default=False,
                        help="Cut off pdf page header ",
                        action="store_true")
    parser.add_argument("--cut_page_footer",
                        default=False,
                        help="Cut off pdf page footer ",
                        action="store_true")
    parser.add_argument("--pdf_host",
                        default="https://historycollection.jsc.nasa.gov/JSCHistoryPortal/history/oral_histories/participants_full.htm",
                        help="The website that will be scraped for pdfs",
                        )

    parser.add_argument("--command", "-c",
                        default="single_file",
                        help="single_file, directory, collect_pdfs, find_astronauts",
                        )
    # All parameters in a file
    parser.add_argument('--parfile',
                        nargs='?',
                        type=str,
                        help='Parameter file')

    args = get_arguments(parser)
    return args


if __name__ == '__main__':
    args = parse_args()

    # --------------------------------------------------------------------------------------------------------
    if (args.version):
        print('--- epubs.py - version 24 feb 2024 ---')
        print('Copyright (C) 2024 - Nico Vermaas. This program comes with ABSOLUTELY NO WARRANTY;')
        sys.exit(0)


    if args.command == 'collect_pdfs':
        collect_pdfs(args)

    if args.command == 'find_astronauts':
        find_astronauts(args)

    if args.command == 'single_file':

        if args.conversion == 'pdf_to_epub':
            # convert a single pdf to a single epub
            single_pdf_to_epub(args)

    # convert a directory with pdf's to a single epub
    if args.command == 'directory':

        if args.conversion == 'pdf_to_epub':
            directory_with_pdf_to_epub(args)

        elif args.conversion == 'pdf_to_txt':
            # convert a directory with pdf's to a single txt
            directory_with_pdf_to_txt(args)

        elif args.conversion == 'html_to_epub':
            # convert a directory with pdf's to a single txt
            directory_with_html_to_epub(args)