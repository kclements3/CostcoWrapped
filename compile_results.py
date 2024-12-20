import pandas as pd

member_ID = 'Replace with Member ID'
df = pd.read_csv('CostcoData_%s.csv'%(member_ID))

unique_ids=set(df['ID'])
out_dict = {'ID': [], 'Name': [], 'Amount': [], 'Times Purchased': []}
for ID in unique_ids:
    df_id =df.loc[df['ID']==ID, :]
    out_dict['ID'].append(ID)
    out_dict['Name'].append(df_id['Name'].iloc[0])
    out_dict['Amount'].append(sum(df_id['Amount']))
    out_dict['Times Purchased'].append(len(df_id.loc[df_id['SaleOrItem']=='Item']))

out_pd = pd.DataFrame.from_dict(out_dict)
out_pd.to_csv('CostcoSummary.csv')