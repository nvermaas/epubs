import os,sys
import argparse
import pypdf

from ebooklib import epub

class MyPDF:
    def __init__(self, filepath):
        self.reader = pypdf.PdfReader(filepath)

    def extract_text(self):
        chapter_text = ""

        count = 0
        for page in self.reader.pages:

            count += 1

            # extracting text from page
            page_text = page.extract_text()

            # replace \n with <br>
            page_text = page_text.replace('\n', '<br>')

            # remove the header of every original pdf page
            if count > 1:
                page_text = page_text.split('<br>', 1)[1]

            # remove the footer and paging of the original pdf (everything after the last <br>)
            page_text = page_text.rsplit('<br>', 1)[0]

            chapter_text = chapter_text + page_text

        #print(chapter_text)
        return chapter_text


class MyBook:
    def __init__(self, args):
        self.book = epub.EpubBook()
        self.book.set_title(args.title)
        self.book.set_language("en")
        self.book.add_author("NASA Oral Histories")

        # create image from the local image
        image_content = open(args.cover_image, "rb").read()
        self.book.set_cover("cover_image.jpg", image_content)

        self.spine = ['nav']
        self.toc = []

    def add_chapter(self, title, chapter_text):

        # create chapter
        count = len(self.spine)
        filename = f"chapter_{count}.xhtml"

        c = epub.EpubHtml(title=title, file_name=filename, lang="en")
        c.content = (
                "<p><img src='cover_image.jpg' alt='Cover Image'/></p>"
                "<h1>" + title + "</h1>"
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
        style = "BODY {color: white;}"
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
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

    # open the pdf and extract the text
    myPDF = MyPDF(args.input)
    chapter_text = myPDF.extract_text()

    # create the epub
    myBook = MyBook(args)

    # add the extracted text from the pdf as a chapter
    filename = os.path.basename(args.input)
    subtitle = os.path.splitext(filename)[0]
    myBook.add_chapter(subtitle, chapter_text)

    # save the epub file
    myBook.save(args)

def directory_with_pdf_to_epub(args):

    # create the epub
    myBook = MyBook(args)

    # Iterate over all files in the directory
    for filename in os.listdir(args.input_directory):
        filepath = os.path.join(args.input_directory, filename)
        subtitle = os.path.splitext(filename)[0]
        extention = os.path.splitext(filename)[1]


        # open the pdf and extract the text
        if extention == '.pdf':
            if args.filter in filename:
                print(f'converting {filepath}...')
                myPDF = MyPDF(filepath)
                chapter_text = myPDF.extract_text()

                subtitle = os.path.splitext(filename)[0]
                myBook.add_chapter(subtitle, chapter_text)

    # save the epub file
    myBook.save(args)

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
            print(parse_args_params)
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
                        default="My book title",
                        help="Title of the epub",
                        )
    parser.add_argument("--cover_image",
                        default=None,
                        help="Cover image of the epub",
                        )
    parser.add_argument("--filter",
                        default=None,
                        help="All pdf's with this substring in the name will be read",
                        )
    parser.add_argument("--command", "-c",
                        default="single_file",
                        help="single_file, directory, scrape_uril",
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
        print('--- epubs.py - version 23 feb 2024 ---')
        print('Copyright (C) 2024 - Nico Vermaas. This program comes with ABSOLUTELY NO WARRANTY;')
        sys.exit(0)

    # convert a single pdf to a single epub
    if args.command == 'single_file':
        single_pdf_to_epub(args)

    # convert a directory with pdf's to a single epub
    if args.command == 'directory':
        directory_with_pdf_to_epub(args)