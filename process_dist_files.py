#!/usr/bin/env python

"""
Take tax files in txt form and format them for CSV
"""

import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

SRC_FILES = os.path.abspath('./DistributionFiles')
DST_FILES = os.path.abspath('./DistributionCSV')


def _fixtup(s):
    """Normalize the string"""
    s = s.strip()
    s = re.sub(r"[^\w\s]", '', s)
    return re.sub(r"\s+", '_', s)

def _subtract_date(date, year=0, month=0):
    """Do the date math"""
    year, month = divmod(year*12 + month, 12)
    if date.month <= month:
        year = date.year - year - 1
        month = date.month - month + 12
    else:
        year = date.year - year
        month = date.month - month
    return date.replace(year = year, month = month)

def _format_adjust_date(d):
    """Adjust FY to CY and format date"""
    d = d[:6] + "01"
    dobj = datetime.strptime(d, '%Y%m%d')
    dobj = _subtract_date(dobj, month=6)
    return dobj.strftime('%Y-%m-%d')

def _add_decimal(n):
    """Given an integer, return with decimal"""
    return n/100

def _read_year_month(d):
    """Returns (year, month) for given YYYY-MM-DD"""
    ymd = d.split("-")
    return (ymd[0], ymd[1])

def _translate_codes():
    """Read codes from the translator and return dictionary"""
    tl = pd.read_excel('Simplified Translator - Sales Tax.xls')
    rd = pd.Series(tl['Component Name'].values, index=tl['Component Code']).to_dict()
    return { x.strip():_fixtup(rd[x]) for x in rd}

def process_distribution_file(dfile):
    """Process distribution txt file and write to csv"""
    df = pd.read_fwf(dfile,
            header=None,
            names=['Date', 'Tax', 'Location', 'Distribution'])
    # Codes to text
    code_lookup = _translate_codes()
    for code in code_lookup:
        df.replace(code, code_lookup[code], inplace=True)

    #Separate Location Code from Location; remove 'SEM' from Date
    df['LocationCode'] = df['Location'].str[:5].apply(np.int64)
    df['Location'] = df['Location'].str[5:]

    df['Date'] = _format_adjust_date(df['Date'].str[:-3][0])

    # Add decimal to distribution and rename distribution column
    df['Distribution'] = df['Distribution'].apply(_add_decimal)
    df.rename(columns = {'Distribution': 'Dollars_Distributed'}, inplace=True)

    if not os.path.exists(DST_FILES):
        os.mkdir(DST_FILES)
    year, month = _read_year_month(df['Date'][0])
    df.to_csv('{}/{}_{}_sales_taxes.csv'.format(DST_FILES, year, month))

if __name__ == '__main__':
    for f in os.listdir(SRC_FILES):
        print("Processing file: {}".format(f))
        try:
            process_distribution_file(os.path.join(SRC_FILES, f))
        except Exception as e:
            print("ERROR: Could not process {}: {}".format(f, str(e)))
