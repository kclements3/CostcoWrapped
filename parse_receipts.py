from pypdf import PdfReader
import regex as re
import pandas as pd
import os


# Record Item number, Item name, and price (including discount)
# Start parsing at first instance of member ID
# End at ****
# Items will be of the format: E? <numbers or whitespace> <letters and/or numbers> <letter or whitespace> <numbers or period>
# Discounts are <numbers>/<numbers> <space> <text> -'

member_ID = 'Replace with ID number on Receipt'
out_dict = {'ID': [], 'Name': [], 'SaleOrItem': [], 'Amount': [], 'Date': []}

# run this script from the same folder as your recipts
files = os.listdir()

# Regex to match a normal item line
item_regex = r'([E\s*])?(\d+)(\s)?(.+?)(\d+\.\d\d)'
# Regex to match a sale  line
sale_regex = r'(\d+)([/\s]+)?([\w\s\d]+) (\d*\.\d\d)'

# subtotal and tax currently unused, but could be added to another structure
subtotal_regex = r'SUBTOTAL(.+)'
tax_regex = r'TAX(.+)'

# If an item is split into two lines, look for these patterns
item_split1_re = r'([EF\s*])?(\d+)(\s)?(.+)'
item_split2_re = r'(\s)?(.+?)(\d+\.\d\d)'

for file in files:
    stop_reading = False
    if file[-3:] == 'pdf':
        # Name of files is of the format Costco_########.pdf
        # the digits represent the date
        date_of_trip = file[7:-4]
        with open(file, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                start_reading = False
                text = page.extract_text()
                second_line = False  # flag to look for second line of multiline item
                for line in text.splitlines():
                    if member_ID in line and not start_reading:
                        start_reading = True
                        continue
                    elif not start_reading or stop_reading:
                        continue
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
                            print('Could not find sale', line, date_of_trip)
                            continue
                        sale_groups = sale.groups()
                        out_dict['ID'].append(out_dict['ID'][-1])
                        out_dict['Name'].append(out_dict['Name'][-1])
                        out_dict['Date'].append(date_of_trip)
                        out_dict['Amount'].append(-float(sale_groups[3]))
                        out_dict['SaleOrItem'].append('Sale')
                    elif start_reading:
                        item = re.search(item_regex, line)
                        if second_line or item is None:
                            if 'https://' in line or 'Orders & Purchases' in line:
                                # These lines can appear on multi-page receipts. Skip them
                                start_reading = False
                                continue
                            # Line is split in two
                            item1 = re.search(item_split1_re, line)
                            item2 = re.search(item_split2_re, line)
                            if item1 is not None and item2 is None:
                                item1_groups = item1.groups()
                                out_dict['ID'].append(item1_groups[1])
                                out_dict['Name'].append(item1_groups[3])
                                out_dict['Date'].append(date_of_trip)
                                second_line = True
                            elif item2 is not None:
                                item2_groups = item2.groups()
                                out_dict['Name'][-1] += item2_groups[1]
                                out_dict['Amount'].append(item2_groups[2])
                                out_dict['SaleOrItem'].append('Item')
                                second_line = False
                            else:
                                print('Could not find item', line, date_of_trip)
                        else:
                            # Normal item line found
                            item_groups = item.groups()
                            out_dict['ID'].append(item_groups[1])
                            out_dict['Name'].append(item_groups[3])
                            out_dict['Date'].append(date_of_trip)
                            out_dict['Amount'].append(float(item_groups[4]))
                            out_dict['SaleOrItem'].append('Item')
                    else:
                        print(line)


out_pd = pd.DataFrame.from_dict(out_dict, dtype=str)
out_pd.to_csv('CostcoData_%s.csv' % (member_ID))