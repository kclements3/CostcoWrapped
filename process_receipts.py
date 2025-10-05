from pypdf import PdfReader
import regex as re
import pandas as pd
import os

class ProcessReceipts:
    def __init__(self):
        self.out_dict = {'ID': [], 'Name': [], 'SaleOrItem': [], 'Amount': [], 'Date': []}
        self.summary_dict = {'Date': [], 'Total': [], 'SubTotal': [], 'Tax': []}

        # Regex to match a normal item line
        self.item_regex = r'([E\s*])?(\d+)(\s)?(.+?) (\d+\.\d\d)'
        self.item_regex_alt = r'([E\s*])?(\d+)(\s)?(.+?)(\d+\.\d\d)'  # No spaces between item & prices

        # Regex to match a sale  line
        self.sale_regex = r'(\d+)([/\s]+)?([\w\s\d]+) (\d*\.\d\d)'
        self.sale_regex_alt = r'(\d+)([/\s]+)?([\w\s\d]+?)(\d*\.\d\d)'  # No spaces between item & prices

        # subtotal and tax currently unused, but could be added to another structure
        self.subtotal_regex = r'SUBTOTAL(.+)'
        self.tax_regex = r'TAX(.+)'
        self.date_regex = r'\d\d/\d\d/\d\d\d\d'

        # Process control flags
        self.results_compiled = False
        self.receipts_processed = False
        self.double_check_list = []

    def get_item(self, line, cur_line) -> (str, bool):
        line = cur_line + line
        if '****' in line:
            return ('', True)
        elif re.match(r'\d-', line[-2:]) is not None:
            # sale item
            sale = re.search(self.sale_regex, line)
            if sale is None:
                sale = re.search(self.sale_regex_alt, line)
                if sale is None:
                    print('Could not find sale', line)
            sale_groups = sale.groups()
            self.out_dict['ID'].append(self.out_dict['ID'][-1])
            self.out_dict['Name'].append(self.out_dict['Name'][-1])
            self.out_dict['Amount'].append(-float(sale_groups[3]))
            self.out_dict['SaleOrItem'].append('Sale')
        elif 'https://' in line or 'Orders & Purchases' in line:
            # These lines can appear on multi-page receipts. Skip them
            return
        else:
            # Normal item line
            item = re.search(self.item_regex, line)
            if item is None:
                item = re.search(self.item_regex_alt, line)
                if item is None:
                    # Item is spit in 2
                    return (line, False)

            item_groups = item.groups()
            self.out_dict['ID'].append(item_groups[1])
            self.out_dict['Name'].append(item_groups[3])
            if float(item_groups[4]) > 1000.0:
                self.double_check_list.append(line)
                print('Double Check', line)
            self.out_dict['Amount'].append(float(item_groups[4]))
            self.out_dict['SaleOrItem'].append('Item')
        return ('', False)

    def parse_receipts(self, receipt_dir):
        files = os.listdir(receipt_dir)
        cur_line = ''
        for file in files:
            stop_reading = False
            stop_items = False
            if file[-3:] == 'pdf':
                with open(receipt_dir+'/'+file, 'rb') as f:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        if stop_reading:
                            break
                        text = page.extract_text()
                        start = re.search(r'Member[\n\s]\d+', text)
                        lines = text[start.span()[1]+1:].splitlines()

                        for line in lines[:-2]:
                            subtot = re.search(self.subtotal_regex, line)
                            tax = re.search(self.tax_regex, line)
                            if subtot is not None:
                                subtotal = subtot.groups()[-1].strip()
                                self.summary_dict['SubTotal'].append(subtotal)
                                continue
                            elif tax is not None:
                                tax = tax.groups()[-1].strip()
                                self.summary_dict['Tax'].append(tax)
                                self.summary_dict['Total'].append(float(subtotal) + float(tax))
                                continue
                            elif not stop_items:
                                cur_line, stop_items = self.get_item(line, cur_line)
                                continue

                            if stop_items:
                                # Done reading items, get total and date
                                date = re.search(self.date_regex, line)
                                if date is not None:
                                    d = line[date.start():date.end()]
                                    self.out_dict['Date'] += [d]*(len(self.out_dict['Name']) - len(self.out_dict['Date']))
                                    self.summary_dict['Date'].append(d)
                                    stop_reading = True
                                    break


        out_pd = pd.DataFrame.from_dict(self.out_dict, dtype=str)
        summary_pd = pd.DataFrame.from_dict(self.summary_dict, dtype=str)
        out_pd.to_csv(f'{receipt_dir}/../CostcoItemData.csv', index=False)
        summary_pd.to_csv(f'{receipt_dir}/../CostcoDataTripSummary.csv', index=False)
        self.parse_gas(receipt_dir + '/gas')
        self.receipts_processed = True


    def parse_gas(self, receipt_dir):
        out_dict = {'Pump': [], 'Gallons': [], 'Price': [], 'Total': [], 'Date': []}

        # run this script from the same folder as your gas recipts
        files = os.listdir(receipt_dir)

        cur_line = ''
        for file in files:
            stop_reading = False
            if file[-3:] == 'pdf':
                # Name of files is of the format Costco_########.pdf
                # the digits represent the date
                with open(receipt_dir+'/'+file, 'rb') as f:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        if stop_reading:
                            break
                        text = page.extract_text()
                        text_split = text.splitlines()
                        info_ind = text_split.index('Pump Gallons Price') + 1
                        pump, gallons, price = text_split[info_ind].split(' ')
                        for line in text_split:
                            if line[0:4] == 'Date':
                                date_of_trip = line[6:]
                        out_dict['Date'].append(date_of_trip)
                        out_dict['Pump'].append(pump)
                        out_dict['Gallons'].append(gallons)
                        out_dict['Price'].append(price)
                        out_dict['Total'].append(float(gallons)*float(price[1:]))
        out_pd = pd.DataFrame.from_dict(out_dict, dtype=str)
        out_pd.to_csv(f'{receipt_dir}/../../CostcoGas.csv',index=False)


    def compile_results(self, receipt_dir):
        df = pd.read_csv(f'{receipt_dir}/../CostcoItemData.csv')

        unique_ids=set(df['ID'])
        out_dict = {'ID': [], 'Name': [], 'Amount': [], 'Times Purchased': []}
        for ID in unique_ids:
            df_id =df.loc[df['ID']==ID, :]
            out_dict['ID'].append(ID)
            out_dict['Name'].append(df_id['Name'].iloc[0])
            out_dict['Amount'].append(sum(df_id['Amount']))
            out_dict['Times Purchased'].append(len(df_id.loc[df_id['SaleOrItem']=='Item']))

        out_pd = pd.DataFrame.from_dict(out_dict)
        out_pd.to_csv(f'{receipt_dir}/../CostcoItemsCompiled.csv', index=False)
        self.results_compiled = True