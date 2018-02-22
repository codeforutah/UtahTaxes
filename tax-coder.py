import pygsheets
# An oauth client_secret.json is needed in the same directory as this file.
gc = pygsheets.authorize()
# Open  a Google spreadsheet by drive ID
spreadsheet = gc.open_by_key('1QA13HliH3YCPgPrmeDLbmw57KCjZbwreSsXGquqmsyU')
sheet1 = spreadsheet.worksheet_by_title("Sheet1")
# Get all values of sheet as 2d list of cells

# You can get a pandas dataframe if it is easier
sheet_dataframe = sheet1.get_as_df(start=(1, 2), end=(48, 3))

# This will create a dictionary with codes as the key
cell_matrix = sheet1.get_values(start=(2, 2), end=(48, 3), returnas='matrix')
code_lookup = {code: name for (code, name) in cell_matrix}
for code in code_lookup:
    print(code + ' : ' + code_lookup[code])
