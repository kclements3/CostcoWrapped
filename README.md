# CostcoWrapped
A way to pull Costco receipts to make a year-end summary of adventures

Steps to make this work:
1. Sign in to Costco.com and go to Orders & Purchases. Click on "View Receipt" for each In-Warehouse purchase.
2. In the top-right, there will be a "Print Receipt" button. Click that and save as pdf. Name each receipt with the format "Costco_mmddyyyy.pdf" where dd is the day, mm is the month, and yyyy is the year. Save these to a folder named "Receipts".
3. Run parse_receipts.py to produce the CostcoData_*.csv file.
4. Ensure the data is correct (products that end in numbers and some sale lines are not correct at this point). Check the console to see if any potential misreads occurred.
5. Run compile_results.py to generate the summary of product purchases.
