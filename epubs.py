import os,sys
import argparse
import pypdf

import ebooklib
from ebooklib import epub

def pdf_to_epub(args):

    # creating a pdf reader object
    reader  = pypdf.PdfReader(args.input)

    chapter_text = ""

    count = 0
    for page in reader.pages:

        count+=1

        # extracting text from page
        page_text = page.extract_text()

        # replace \n with <br>
        page_text = page_text.replace('\n','<br>')

        # remove the header of every original pdf page
        if count>1:
            page_text = page_text.split('<br>',1)[1]

        # remove the footer and paging of the original pdf (everything after the last <br>)
        page_text = page_text.rsplit('<br>', 1)[0]

        chapter_text = chapter_text + page_text
        print(page_text)
        print('--------------------------------------')

    # create the epub file
    book = epub.EpubBook()
    book.set_title(args.title)
    book.set_language("en")
    book.add_author("NASA Oral Histories")
    book.set_cover("input_pdf\cover.jpg","NASA Oral Histories")

    # create image from the local image
    image_content = open("input_pdf\cover.jpg", "rb").read()
    img = epub.EpubImage(
        uid="image_1",
        file_name="static/cover.jpg",
        media_type="image/gif",
        content=image_content,
    )


    # create chapter
    c1 = epub.EpubHtml(title="Joe", file_name="chap_01.xhtml", lang="hr")
    c1.content = (
        "<h1>" + args.title + "</h1>"
        "<p>" + chapter_text + "</p>"
    )


    # add chapter
    book.add_item(c1)
    # add image
    book.add_item(img)

    # define Table Of Contents
    book.toc = (
        epub.Link("chap_01.xhtml", "Joe Allen", "intro"),
    )

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    style = "BODY {color: white;}"
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    book.spine = ["nav", c1]

    # write to the file
    epub.write_epub(args.output, book, {})


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
    parser.add_argument("--output", "-o",
                        default=None,
                        help="output epub file",
                        )
    parser.add_argument("--title",
                        default="My book title",
                        help="Title of the epub",
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


    if args.command == 'single_file':
        pdf_to_epub(args)