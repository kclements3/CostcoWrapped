# CostcoWrapped
A way to pull Costco receipts to make a year-end summary of adventures

Steps to make this work:
1. Sign in to Costco.com and go to Orders & Purchases. Click on "View Receipt" for each In-Warehouse purchase.
2. In the top-right, there will be a "Print Receipt" button. Click that and save as pdf. Save all receipts to a common folder.
3. Do the same with the gas receipts. Save these to a folder named "gas" inside the main "Receipts" folder you just made in step 2.
4. Run CostcoWrapped.py to launch the GUI. This will prompt you to select the folder of receipts and process the results.
5. After pressing the "Process Receipts" button, a file named CostcoData.csv will be saved in the main folder where you ran this script. Any items that could've been interpreted incorrectly will be displayed in the center window.
6. Modify/check CostcoData.csv to fix any errors (usually items that end with a number will be misinterpreted as very large prices). Save this file.
7. After verifying CostcoData.csv looks correct, click "Compile" in the bottom right of the GUI. This will create CostcoSummary.csv with all the items you purchased for the year.
8. Gas Data and overall trip data are also saved in CostcoGas.csv and CostcoDataSummary2025.csv.
9. Put together a fun powerpoint with your results!
