# CostcoWrapped
A way to pull Costco receipts to make a year-end summary of adventures

Steps to make this work:
1. Sign in to Costco.com and go to Orders & Purchases. Click on "View Receipt" for each In-Warehouse purchase.
2. In the top-right, there will be a "Print Receipt" button. Click that and save as pdf. Name each receipt with the format "Costco_mmddyyyy.pdf" where dd is the day, mm is the month, and yyyy is the year. Save these to this folder
3. In parse_receipts.py, input your member ID into the member_ID variable.
4. Run parse_receipts.py to produce the CostcoData_*.csv file.
5. Ensure the data is correct (products that end in numbers and some sale lines are not correct at this point). Check the console to see if any items weren't read at all.
6. Once the data is correct in the CostcoData file, edit compile_results.py to add your member_ID to that file as well.
7. Run compile_results.py to generate the summary of product purchases.
