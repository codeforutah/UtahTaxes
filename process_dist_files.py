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
DST_FILE = os.path.abspath('./TaxDataFull.csv')


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

def _extract_legacy_loc(c):
    """Return location string"""
    return c[12:]

def _extract_legacy_loc_code(c):
    """Returns location code int"""
    return np.int64(c[7:12])

def _legacy_file(dframe):
    """Process legacy file with only two columns (example below)"""
    # 200901G11000Iron County               00004213516
    date_code = _format_adjust_date(dframe['Date'][:6][0])
    # Fill in Location and Distribution first
    dframe['Location'] = dframe['Date'].apply(_extract_legacy_loc)
    dframe['Dollars_Distributed'] = dframe['Tax'].apply(_add_decimal)
    dframe['LocationCode'] = dframe['Date'].apply(_extract_legacy_loc_code)
    dframe['Tax'] = 'unknown'
    dframe['Date'] = date_code

    return dframe


def process_distribution_file(dfile, codes):
    """Process distribution txt file and write to csv"""
    df = pd.read_fwf(dfile,
            header=None,
            names=['Date', 'Tax', 'Location', 'Dollars_Distributed'])

    # Legacy files only have two columns
    if df['Location'].isnull().all() and df['Dollars_Distributed'].isnull().all():
        return _legacy_file(df)

    # Codes to text
    for code in codes:
        df.replace(code, codes[code], inplace=True)

    #Separate Location Code from Location; remove 'SEM' from Date
    df['LocationCode'] = df['Location'].str[:5].apply(np.int64)
    df['Location'] = df['Location'].str[5:]

    df['Date'] = _format_adjust_date(df['Date'].str[:-3][0])

    # Add decimal to distribution and rename distribution column
    df['Dollars_Distributed'] = df['Dollars_Distributed'].apply(_add_decimal)

    return df

def write_csv(dframe, loc):
    if os.path.isfile(loc):
        dframe.to_csv(loc, index=False, mode='a', header=False)
    else:
        dframe.to_csv(loc, index=False, mode='w')


if __name__ == '__main__':
    code_lookup = _translate_codes()
    for f in os.listdir(SRC_FILES):
        print("Processing file: {}".format(f))
        try:
            rdf = process_distribution_file(os.path.join(SRC_FILES, f), code_lookup)
        except Exception as e:
            print("ERROR: Could not process {}: {}".format(f, str(e)))
        else:
            write_csv(rdf, DST_FILE)
