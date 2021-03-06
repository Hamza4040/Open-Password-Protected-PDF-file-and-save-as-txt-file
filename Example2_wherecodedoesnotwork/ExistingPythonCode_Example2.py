import re
import os
import math
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams, LTTextBox, LTTextBoxHorizontal, LTTextLineHorizontal, LTChar
from pdfminer.pdfdocument import PDFDocument, PDFPasswordIncorrect

# Path that contains the PDF files that will be processed
source_path = r'PDF_Files_Loaded'

# Path onto which the script will write its output text file
destination_path = r'Txt_Files_Converted'

# File names that match the below wildcard, would be processed
wild_card = re.compile(r'.*(381837904|381861673|381851551).*[.]pdf$', re.IGNORECASE)

# If a file needs password, it should be the one below
password = '2003/024082/07'

TEXT_ELEMENTS = [
    LTTextBox,
    LTTextBoxHorizontal
]


def flatten(lst):
    """
    Flattens a list of lists
    """
    return [subelem for elem in lst for subelem in elem]


def extract_words(element):
    """
    Recursively extracts individual words from
    text elements.
    """
    if isinstance(element, LTTextLineHorizontal) and any([isinstance(e, LTChar) for e in element]):
        return [element]

    elif isinstance(element, LTTextLineHorizontal):
        return flatten([extract_words(e) for e in element])

    if any(isinstance(element, i) for i in TEXT_ELEMENTS):
        return flatten([extract_words(e) for e in element])

    if isinstance(element, list):
        return flatten([extract_words(l) for l in element])

    return []


def get_page_words_sorted_and_layout(page):
    """
     Given a PDF page, returns a list of words sorted by
     Y coordinates descendingly then on X coordinates ascendingly
     """
    interpreter.process_page(page)
    layout = device.get_result()
    # Get all words in the page
    texts = []
    for e in layout:
        if isinstance(e, LTTextBoxHorizontal):
            texts.append(e)

    words = extract_words(texts)
    words.sort(key=lambda w: (round(-w.bbox[3]), w.bbox[0]))
    return words, layout


for filename in os.listdir(source_path):
    if wild_card.match(filename) is not None:
        try:
            out_fname = os.path.splitext(filename)[0] + '.txt'
            out_path = os.path.join(destination_path, out_fname)
            with open(out_path, 'w', encoding='utf-8') as f:
                complete_fname = os.path.join(source_path, filename)
                fp = open(complete_fname, 'rb')
                parser = PDFParser(fp)
                try:
                    document = PDFDocument(parser, password)
                except PDFPasswordIncorrect:
                    document = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                laparams = LAParams()
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                pages = PDFPage.create_pages(document)
                for page in pages:
                    words, layout = get_page_words_sorted_and_layout(page)
                    out_lines = []
                    last_y = -math.inf
                    for word in words:
                        cur_y = word.bbox[3]
                        cur_x_st = word.bbox[0]
                        cur_x_ed = word.bbox[2]
                        text = word.get_text()
                        if abs(cur_y - last_y) > 3:
                            out_lines.append([(cur_x_st, cur_x_ed, text)])
                            last_y = cur_y
                        else:
                            out_lines[-1].append((cur_x_st, cur_x_ed, text))

                    out_lines = [sorted(lst) for lst in out_lines]
                    space_w = 4
                    for line in out_lines:
                        txt = ''
                        cur_st_x = 0
                        ed = layout.bbox[2]
                        for x_st, x_ed, text in line:
                            # Round X values to the nearest multiple of space width
                            x_st = round(x_st / space_w) * space_w
                            x_ed = round(x_ed / space_w) * space_w
                            n_spaces = (x_st - cur_st_x) / space_w
                            txt += ' ' * round(n_spaces)
                            txt += text.strip()
                            cur_st_x = x_ed
                        f.write(txt+'\n')
                    f.write('====================================================')
                    f.write('====================================================')
                    f.write('====================================================')
                    f.write('====================================================\n')

        except Exception as e:
            print(e)
