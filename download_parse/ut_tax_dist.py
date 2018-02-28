#!/usr/bin/python

'''
!!! WARNING !!!

This script will overwrite PDF and text files in your current working directory

!!! WARNING !!!

Incorrect use of this script could overwhelm a government server -- use at your
own risk!

Assumes the binary 'pdftotext' is in your $PATH

Usage - parse existing PDFs:            ut_tax_dist.py
Usage - download and then parse PDFs:   ut_tax_dist.py download

Send bugs to Mathew White <mathew.b.white@gmail.com>

TODO: Fix assumption regarding column names (assumes every file is the same)

'''

import re
import csv
import sys
import glob
import time
import shutil
import os.path
import requests
from bs4 import BeautifulSoup
from subprocess import check_output

# Column Format
cols = (
    'jcode city tot_dist tot_ded fin_dist '
    'bal_owe tot_paid bal_fwd'
).split(' ')
print(cols)


# Trim unwanted characters (leading/trailing spaces, commas, dollar-signs)
def trimit(v):
    return re.sub(r'(^\s+|\s+$|[,\$])', '', v)


# Convert a formatted line to an array
def line2cols(line):
    ary = list(re.match(
        (
            r'^\s+(\d{5})'          # Jurisdiction Code
            r'\s+([^\$]+)'          # City
            r'([\$\d\,\.-]+)\s+'    # Tot Dist
            r'([\$\d\,\.-]+)\s+'    # Tot Dec
            r'([\$\d\,\.-]+)\s+'    # Fin Dist
            r'([\$\d\,\.-]+)\s+'    # Bal Owe
            r'([\$\d\,\.-]+)\s+'    # Tot Pay
            r'([\$\d\,\.-]+)'       # Bal Fwd
        ),
        line
    ).group(*range(1, 9)))
    return list(map(trimit, ary))


# Parse all the given text files
def parseit(txts):
    stor = []
    for t in txts:
        print("Processing %s" % t)
        (y, m, tax) = re.match(r'\./(\d\d)(\d\d)(.*)\.txt', t).group(1, 2, 3)
        y = '20' + y
        print("Year: %s Month: %s Tax: %s" % (y, m, tax))
        with open(t, 'r') as file:
            for line in file:
                if re.match(r'^\s+\d{5}', line):
                    ary = line2cols(line)
                    stor.append([y, m, tax] + ary)
    return stor


# Save all the parsed data
def storeit(stor):
    with open('ut_tax.csv', 'wb') as csvfile:
        wr = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        wr.writerow(['year', 'month', 'tax'] + cols)
        for s in stor:
            wr.writerow(s)


# Get all the PDF files from the salestax PDF links on the give URL
def getfiles(url):
    # Get the main URL
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    # For each PDF link, download it if it doesn't already exist
    for link in soup.find_all('a'):
        ref = link.get('href')
        if ref is not None and re.match(r'/salestax/distribute/\d\d\d\d', ref):
            # Get the filename from the path
            # For security, ensure filename has only desired characters
            fn = re.match(
                r'/salestax/distribute/(\d\d\d\d[\w\-\.]+)',
                ref
            ).group(1)

            # Check to see if we already downloaded it
            if os.path.isfile(fn):
                print("%s is already downloaded" % fn)
                continue

            # Get the file and save it
            print('Get %s FN %s' % (ref, fn))
            r = requests.get(
                ('https://tax.utah.gov%s' % ref),
                verify=False, stream=True
            )

            if r.status_code == 200:
                with open(fn, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                print("Skipping %s due to error!" % fn)

            # Put in a timer to prevent a denial of service block
            time.sleep(3)


if __name__ == '__main__':

    # Assumes your current working directory contains the PDFs you wish to use
    # See WARNING at top of script

    # If the 'download' argument was given to this script, download the PDFs
    if len(sys.argv) > 1 and sys.argv[1] == 'download':
        getfiles('https://tax.utah.gov/sales/distribution')

    # Get PDF files
    pdfs = glob.glob('./*.pdf')

    # Convert PDF files to formatted text
    for p in pdfs:
        check_output("pdftotext -layout %s" % p, shell=True)
        print("Processed %s" % p)

    # Now that each PDF is processed, we have a lot of text files to process

    # Get text files
    txts = glob.glob('./*.txt')

    # Parse the text files
    stor = parseit(txts)

    # Store the parsed data as CSV
    storeit(stor)
