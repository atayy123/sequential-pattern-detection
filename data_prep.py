import pandas as pd

dt = pd.read_csv("dataframe.csv")

# delete ABORTED tests
dt = dt[dt.RESULT != "ABORTED"]

# modify fail messages for easier search
aa = dt.MESSAGE.str.replace("***","|")
aa = aa.str.get_dummies().add_prefix("E-")

# failed tests for easier search
ac = dt.FAILED.str.get_dummies(sep=' ').add_prefix("F-")

# write test orders as sequence indices
ab = dt.SEQUENCE.str.get_dummies(sep=' ')
ab = ab.replace(0, "-")

# delete test runs without sequence
drop_list = []

for ind, row in dt.iterrows():
    if type(row.SEQUENCE) == str:
        if row.SEQUENCE == "":
            drop_list.append(ind)
        else:
            t_list = row.SEQUENCE.split(" ")
            for pointer, test in enumerate(t_list):
                ab[test].loc[ind] = pointer + 1
    else:
        drop_list.append(ind)

# create a new dataframe for detailed sequence analysis
new_dt = pd.concat([dt, aa, ab, ac], axis=1)
new_dt = new_dt.drop(drop_list)
new_dt = new_dt.drop("SEQUENCE", axis = 1)
new_dt = new_dt.drop("FAILED", axis = 1)
new_dt = new_dt.drop("MESSAGE", axis = 1)

# save the modified dataframe
new_dt.to_csv("modified_dataframe.csv")
print("Dataframe is modified and written to modified_dataframe.csv")

# create another dataframe for sequence mining
oth_dt = pd.concat([dt.BUILD_ID, dt.RESULT, dt.SEQUENCE, ac],axis=1)
oth_dt = oth_dt.drop(drop_list)

# save the other dataframe
oth_dt.to_csv("seq_analysis.csv")
print("Test order sequences are written to seq_analysis.csv")

print("Data preprocessing complete")