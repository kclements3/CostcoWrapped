import os
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import tkinter.font as tkFont

# from process_receipts import *
from process_receipts import ProcessReceipts


class CostcoWrappedGUI:
    def __init__(self):
        # Read in logo
        image_path = "img/Wrapped_img.png"
        original_image = Image.open(image_path)
        resized_image = original_image.resize((230, 130), Image.LANCZOS)

        # Main window
        self.root = Tk()

        # Add image logo
        image = PhotoImage(file=image_path)
        tk_image = ImageTk.PhotoImage(resized_image)
        image_label = Label(self.root, image=tk_image)
        image_label.image = tk_image
        image_label.grid(row=0, column=0, columnspan=2)

        # Get the default font object
        default_font = tkFont.nametofont("TkDefaultFont")
        # Configure the default font
        default_font.configure(family="Futura", size=12)

        self.root.title("Costco Wrapped")
        self.receipt_dir = StringVar()

        self.processor = ProcessReceipts()

    def process_receipts_wrapper(self):
        self.processor.parse_receipts(self.receipt_dir.get())
        if self.processor.receipts_processed:
            self.check_val_label.config(
                text='Processing Complete! Check all values in CostcoData2025_test.csv. Gas is in CostcoGas2025.csv.')
            self.comp_button['state'] = NORMAL

        for item in self.processor.double_check_list:
            self.lb.insert(END, 'Double Check {}'.format(item))

    def compile_results_wrapper(self):
        self.processor.compile_results()
        if self.processor.results_compiled:
            success_label=Label(self.root, text='Results are compiled in CostcoSummary.csv!')
            success_label.grid(column=0, row=6, sticky=W)

    def create_grid(self):
        rows = 5
        cols = 2

        # First Row
        Label(self.root, text='After downloading all receipts to the your “receipts” folder, select it:').grid(column=0,
                                                                                                          row=1,
                                                                                                          sticky=W)

        # Create a button to trigger the folder browsing
        browse_button = Button(self.root, text="Browse Folder", command=self.browse_folder)
        browse_button.grid(column=1, row=1, sticky=W)

        # Second Row
        self.folder_label = Label(self.root, text='Select Folder')
        self.folder_label.grid(column=0, row=2, sticky=W)
        self.process_button = Button(self.root, text="Process Receipts", command=self.process_receipts_wrapper)
        self.process_button.grid(column=1, row=2, sticky=W)
        self.process_button['state'] = DISABLED

        # Third Row
        self.check_val_label = Label(self.root, text='Select Folder')
        self.check_val_label.grid(column=0, row=3, sticky=W, columnspan=2)

        # Fourth Row: list any items needing double checking
        self.lb = Listbox(self.root, width=50)
        self.lb.grid(column=0, row=4, columnspan=2, sticky=W)

        # Fourth Row
        temp = Label(self.root, text='If all looks good, compile results:')
        temp.grid(column=0, row=5, sticky=W)

        self.comp_button = Button(self.root, text="Compile", command=self.compile_results_wrapper)
        self.comp_button.grid(column=1, row=5, sticky=W)
        self.comp_button['state'] = DISABLED

    def browse_folder(self):
        """Opens a folder selection dialog and prints the selected path."""
        f = filedialog.askdirectory()
        self.receipt_dir.set(f)
        if self.receipt_dir:  # Check if a folder was selected (not cancelled)
            self.folder_label.config(text=self.receipt_dir.get())
            self.process_button['state'] = NORMAL