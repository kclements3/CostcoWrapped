from pypdf import PdfReader
import regex as re
import pandas as pd
import os
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import tkinter.font as tkFont


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
    date_regex = r'\d\d/\d\d/\d\d\d\d'

    cur_line = ''
    for file in files:
        stop_reading = False
        stop_items = False
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
                            stop_items = True
                        elif subtot is not None:
                            subtotal = subtot.groups()[-1].strip()
                            continue
                        elif tax is not None:
                            tax = tax.groups()[-1].strip()
                            continue

                        if stop_items:
                            # Done reading items, get total and date
                            date = re.search(date_regex, line)
                            if date is not None:
                                d = line[date.start():date.end()]
                                out_dict['Date'] += [d]*(len(out_dict['Name']) - len(out_dict['Date']))
                                stop_reading = True
                                break
                        elif re.match(r'\d-', line[-2:]) is not None:
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
                            if float(item_groups[4]) > 1000.0:
                                lb.insert(END, 'Double Check {} from {}'.format(line, date_of_trip))
                                print('Double Check', line)
                            out_dict['Amount'].append(float(item_groups[4]))
                            out_dict['SaleOrItem'].append('Item')
                            second_line = False


    out_pd = pd.DataFrame.from_dict(out_dict, dtype=str)
    out_pd.to_csv('CostcoData2025.csv', index=False)
    parse_gas(receipt_dir + '/gas')
    check_val_label.config(text='Processing Complete! Check all values in CostcoData2025_test.csv. Gas is in CostcoGas2025.csv.')
    comp_button['state'] = NORMAL


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
    out_pd.to_csv('CostcoGas2025.csv',index=False)


def browse_folder():
    """Opens a folder selection dialog and prints the selected path."""
    f = filedialog.askdirectory()
    receipt_dir.set(f)
    if receipt_dir:  # Check if a folder was selected (not cancelled)
        folder_label.config(text=receipt_dir.get())
        process_button['state'] = NORMAL

def compile_results():
    df = pd.read_csv('CostcoData2025.csv')

    unique_ids=set(df['ID'])
    out_dict = {'ID': [], 'Name': [], 'Amount': [], 'Times Purchased': []}
    for ID in unique_ids:
        df_id =df.loc[df['ID']==ID, :]
        out_dict['ID'].append(ID)
        out_dict['Name'].append(df_id['Name'].iloc[0])
        out_dict['Amount'].append(sum(df_id['Amount']))
        out_dict['Times Purchased'].append(len(df_id.loc[df_id['SaleOrItem']=='Item']))

    out_pd = pd.DataFrame.from_dict(out_dict)
    out_pd.to_csv('CostcoSummary2025.csv', index=False)
    success_label=Label(root, text='Results are compiled in CostcoSummary.csv!')
    success_label.grid(column=0, row=6, sticky=W)
    # success_label.configure(bg='white')

def create_grid(root):
    global folder_label
    global process_button
    global check_val_label
    global comp_button
    global lb
    rows = 5
    cols = 2

    # First Row
    Label(root, text='After downloading all receipts to the your “receipts” folder, select it:').grid(column=0, row=1, sticky=W)

    # Create a button to trigger the folder browsing
    browse_button = Button(root, text="Browse Folder", command=browse_folder)
    browse_button.grid(column=1, row=1, sticky=W)

    # Second Row
    folder_label = Label(root, text='Select Folder')
    folder_label.grid(column=0, row=2, sticky=W)
    process_button = Button(root, text="Process Receipts", command= lambda: parse_receipts(receipt_dir.get()))
    process_button.grid(column=1, row=2, sticky=W)
    # process_button.configure(bg='white')
    process_button['state'] = DISABLED

    # Third Row
    check_val_label = Label(root, text='Select Folder')
    check_val_label.grid(column=0, row=3, sticky=W, columnspan=2)

    # Fourth Row: list any items needing double checking
    lb = Listbox(root, width=50)
    lb.grid(column=0, row=4, columnspan=2, sticky=W)

    # Fourth Row
    temp=Label(root, text='If all looks good, compile results:')
    temp.grid(column=0, row=5, sticky=W)
    # temp.configure(bg='white')

    comp_button = Button(root, text="Compile", command= compile_results)
    comp_button.grid(column=1, row=5, sticky=W)
    # comp_button.configure(bg='white')
    comp_button['state'] = DISABLED


if __name__ == '__main__':
    # Read in logo
    image_path = "img/Wrapped_img.png"
    original_image = Image.open(image_path)
    resized_image = original_image.resize((230, 130), Image.LANCZOS)

    # Main window
    root = Tk()

    # Add image logo
    tk_image = ImageTk.PhotoImage(resized_image)
    image_label = Label(root, image=tk_image)
    image_label.grid(row=0,column=0, columnspan=2)

    # Get the default font object
    default_font = tkFont.nametofont("TkDefaultFont")

    # Configure the default font
    default_font.configure(family="Futura", size=12)

    root.title("Costco Wrapped")
    receipt_dir = StringVar()
    create_grid(root)

    root.mainloop()
