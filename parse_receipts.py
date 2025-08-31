from pypdf import PdfReader
import regex as re
import pandas as pd
import os


# Record Item number, Item name, and price (including discount)
# Start parsing at first instance of member ID
# End at ****
# Items will be of the format: E? <numbers or whitespace> <letters and/or numbers> <letter or whitespace> <numbers or period>
# Discounts are <numbers>/<numbers> <space> <text> -'

# Add stats on trip totals (number of items, price, discount total)
def parse_receipts(receipt_dir):
    out_dict = {'ID': [], 'Name': [], 'SaleOrItem': [], 'Amount': [], 'Date': []}

    # run this script from the same folder as your recipts
    files = os.listdir(receipt_dir)

    # Regex to match a normal item line
    item_regex = r'([E\s*])?(\d+)(\s)?(.+?) (\d+\.\d\d)'
    item_regex_alt = r'([E\s*])?(\d+)(\s)?(.+?)(\d+\.\d\d)'  # No spaces between item & prices

    # Regex to match a sale  line
    sale_regex = r'(\d+)([/\s]+)?([\w\s\d]+) (\d*\.\d\d)'
    sale_regex_alt =r'(\d+)([/\s]+)?([\w\s\d]+?)(\d*\.\d\d)' # No spaces between item & prices

    # subtotal and tax currently unused, but could be added to another structure
    subtotal_regex = r'SUBTOTAL(.+)'
    tax_regex = r'TAX(.+)'

    cur_line = ''
    for file in files:
        stop_reading = False
        if file[-3:] == 'pdf':
            # Name of files is of the format Costco_########.pdf
            # the digits represent the date
            date_of_trip = file[7:-4]
            with open(receipt_dir+'/'+file, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    if stop_reading:
                        break
                    text = page.extract_text()
                    second_line = False  # flag to look for second line of multiline item
                    start = re.search(r'Member[\n\s]\d+', text)
                    lines = text[start.span()[1]+1:].splitlines()

                    for line in lines[:-2]:
                        if second_line:
                            line = cur_line + line

                        subtot = re.search(subtotal_regex, line)
                        tax = re.search(tax_regex, line)
                        if '****' in line:
                            stop_reading = True
                            break
                        elif subtot is not None:
                            subtotal = subtot.groups()[-1].strip()
                            continue
                        elif tax is not None:
                            tax = tax.groups()[-1].strip()
                            continue

                        if re.match(r'\d-', line[-2:]) is not None:
                            # sale item
                            sale = re.search(sale_regex, line)
                            if sale is None:
                                sale = re.search(sale_regex_alt, line)
                                if sale is None:
                                    print('Could not find sale', line, date_of_trip)
                                    continue
                            sale_groups = sale.groups()
                            out_dict['ID'].append(out_dict['ID'][-1])
                            out_dict['Name'].append(out_dict['Name'][-1])
                            out_dict['Date'].append(date_of_trip)
                            out_dict['Amount'].append(-float(sale_groups[3]))
                            out_dict['SaleOrItem'].append('Sale')
                        elif 'https://' in line or 'Orders & Purchases' in line:
                            # These lines can appear on multi-page receipts. Skip them
                            continue
                        else:
                            # Normal item line
                            item = re.search(item_regex, line)
                            if item is None:
                                item = re.search(item_regex_alt, line)
                                if item is None:
                                    # Item is spit in 2
                                    second_line = True
                                    cur_line = line
                                    continue

                            item_groups = item.groups()
                            out_dict['ID'].append(item_groups[1])
                            out_dict['Name'].append(item_groups[3])
                            out_dict['Date'].append(date_of_trip)
                            if float(item_groups[4]) > 1000.0:
                                print('Double Check', line)
                            out_dict['Amount'].append(float(item_groups[4]))
                            out_dict['SaleOrItem'].append('Item')
                            second_line = False


    out_pd = pd.DataFrame.from_dict(out_dict, dtype=str)
    out_pd.to_csv('CostcoData2025.csv')

def parse_gas(receipt_dir):
    out_dict = {'Pump': [], 'Gallons': [], 'Price': [], 'Total': [], 'Date': []}

    # run this script from the same folder as your gas recipts
    files = os.listdir(receipt_dir)

    cur_line = ''
    for file in files:
        stop_reading = False
        if file[-3:] == 'pdf':
            # Name of files is of the format Costco_########.pdf
            # the digits represent the date
            date_of_trip = file[4:-4]
            with open(receipt_dir+'/'+file, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    if stop_reading:
                        break
                    text = page.extract_text()
                    text_split = text.splitlines()
                    info_ind = text_split.index('Pump Gallons Price') + 1
                    pump, gallons, price = text_split[info_ind].split(' ')
                    out_dict['Date'].append(date_of_trip)
                    out_dict['Pump'].append(pump)
                    out_dict['Gallons'].append(gallons)
                    out_dict['Price'].append(price)
                    out_dict['Total'].append(float(gallons)*float(price[1:]))
    out_pd = pd.DataFrame.from_dict(out_dict, dtype=str)
    out_pd.to_csv('CostcoGas2025.csv',index=False)

if __name__ == '__main__':
    receipt_dir = 'Receipts2025'
    parse_receipts(receipt_dir)

    gas_dir = receipt_dir + '/gas'
    parse_gas(gas_dir)
