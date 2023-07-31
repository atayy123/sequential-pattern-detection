from SPADE import SPADE
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def count_fails(data):
    """Counts the number of failed tests in the modified dataframe. Input the sliced version of the modified dataframe."""

    fails = data[data.columns[pd.Series(data.columns).str.startswith("F-")]]
    fails = fails.sum(axis=0)
    fails = fails[fails != 0]
    fails.index = fails.index.str.removeprefix("F-")
    fails = fails.sort_values(ascending=False)
    
    return fails

def count_msg(data):
    """Counts the number of error messages in the modified dataframe. Input the sliced version of the modified dataframe."""
    
    message_list = data[data.columns[pd.Series(data.columns).str.startswith("E-")]]
    message_list = message_list.sum(axis=0)
    message_list = message_list[message_list != 0]
    message_list.index = message_list.index.str.removeprefix("E-")
    message_list = message_list.sort_values(ascending=False)
    
    return message_list

def spade_mine(start_id, end_id, minSup, maxSup, writeFile=False):
    """
    Description:
    -------------
    Detects sequential patterns of the failed and successful test cases using the
    SPADE algorithm. Range of the tests are given with start_id and end_id. These
    correspond to the BUILD_ID.

    Patterns are taken if they have higher support than minSup (for failed cases)
    or maxSup (for successful cases).

    Then, the useless patterns are eliminated.

    Parameters:
    -------------
    start_id: BUILD_ID of the first test
    end_id: BUILD_ID of the last test
    minSup: Minimum support for the failed tests.
    maxSup: Minimum support for the successful tests.
    writeFile: If True, writes the patterns to CSV files.

    Returns:
    -------------
    Returns the frequent patterns.
    """

    separator = " "

    # import the dataframe and get the tests with BUILD_ID between start_id and end_id
    dt = pd.read_csv("seq_analysis.csv")
    dt.drop("Unnamed: 0", axis=1, inplace=True)
    dt = dt[(dt.BUILD_ID >= start_id) & (dt.BUILD_ID <= end_id)]

    if dt.empty:
        print("No data found. Give appropriate start and end ID values.")
    else:
        # separate the successful and failed test runs
        seq_vals = dt[dt.RESULT == "FAILURE"]
        seq_success = dt[dt.RESULT == "SUCCESS"].SEQUENCE

        # find patterns in Failed tests, with higher support than minSup
        # get the Failed tests first, see how many tests have failed
        fails = seq_vals[seq_vals.columns[seq_vals.columns.str.startswith("F-")]]
        fails = fails.sum(axis=0)
        print("Total number of failed tests:")
        print(fails)

        # only get the tests which has failed more than minSup
        minsupnum = round(float(minSup) * len(seq_vals))
        print("")
        print("Required fail number:", minsupnum)
        print("")
        
        fails = fails[fails >= minsupnum]

        if fails.empty:
            print("Not enough failed tests. Try a larger range or lower min support.")
        else:
            # list of failed tests higher than threshold
            fails = fails.index.to_list()

            # create an empty dataframe for patterns
            f_df = pd.DataFrame(columns=["Patterns", "Support"])

            # iterate over these failed tests
            for fail in fails:
                t_fail = " " + fail.replace("F-", "") + " "
                temp = seq_vals[seq_vals[fail] == 1].SEQUENCE.str.split(t_fail)
                temp = pd.Series([i[0] + t_fail.rstrip() for i in temp])

                # initialize SPADE algorithm
                f_spade = SPADE(iFile=temp, minSup=minsupnum, sep=separator)
                # start mining
                f_spade.startMine()
                
                # get detected patterns
                f_pattern_df = f_spade.getPatternsAsDataFrame()

                f_pattern_df.Patterns = f_pattern_df.Patterns.str.replace("(", "")
                f_pattern_df.Patterns = f_pattern_df.Patterns.str.replace(")", "")
                f_pattern_df.Patterns = f_pattern_df.Patterns.str.replace("'", "")
                f_pattern_df.Patterns = f_pattern_df.Patterns.str.split(", ")

                drop_list = []

                for ind in range(len(f_pattern_df)):
                    sel = f_pattern_df.Patterns.iloc[ind]
                    
                    # delete the patterns with length 1
                    if len(sel) == 1:
                        drop_list.append(ind)
                    # delete the patterns which doesnt have the failed test as last element
                    if sel[-1] != t_fail.strip():
                        drop_list.append(ind)

                f_pattern_df.drop(drop_list, axis=0, inplace=True)
                
                f_df = pd.concat([f_df, f_pattern_df], ignore_index=True)

            if f_df.empty:
                print("No patterns found for failed cases. Change support or range.")
            else:
                print("Number of patterns in failed cases with support", minSup, "=>", len(f_df), "\n")

                # calculate the percentage of support and add to dataframe
                supp = f_df.Support / len(seq_vals)
                f_df["SupportPerc"] = supp

                # calculate the length of patterns and add to dataframe
                len_list = [len(t) for t in f_df.Patterns.values]
                f_df["Length"] = len_list

                # transform list to string
                f_df.Patterns = f_df.Patterns.apply(lambda x: " ".join(x))

                # sort by support
                f_df = f_df.sort_values("Support", ascending=False)

                f_df_before = f_df.copy()

                if writeFile:
                    # write to csv
                    f_df.to_csv("fail_patterns.csv")

                # find Patterns in Successful tests, with higher support than maxSup

                # initialize
                s_spade = SPADE(iFile=seq_success, minSup=maxSup, sep=separator)
                # start mining
                s_spade.startMine()
                # get detected patterns in a dataframe
                s_pattern_df = s_spade.getPatternsAsDataFrame()

                s_pattern_df.Patterns = s_pattern_df.Patterns.str.replace("(", "")
                s_pattern_df.Patterns = s_pattern_df.Patterns.str.replace(")", "")
                s_pattern_df.Patterns = s_pattern_df.Patterns.str.replace("'", "")
                s_pattern_df.Patterns = s_pattern_df.Patterns.str.replace(",", "")

                # calculate the percentage of support and add to dataframe
                supp = s_pattern_df.Support / len(seq_success)
                s_pattern_df["SupportPerc"] = supp

                print("Number of patterns in successful cases with support", maxSup, "=>", len(s_pattern_df), "\n")

                if writeFile:
                    s_pattern_df.to_csv("success_patterns.csv")
                    print("CSV files containing patterns with", minSup, "(for fails) and", maxSup, "(for success) support are created successfully. \n")

                # Prune unrelevant patterns
                # Step 1: Delete patterns that has higher support in Success cases
                
                success_pats = s_pattern_df.Patterns.values

                print("Failed patterns length:", len(f_df))

                # indices of patterns that will be deleted
                drop_list = []

                # iterate over failed patterns
                for index, patt in f_df.Patterns.items():
                # check if the same pattern is in success case
                    if patt in success_pats:
                        ind = np.where(success_pats == patt)
                        # find support percentage values
                        s_support = s_pattern_df.SupportPerc.iloc[ind].values
                        f_support = f_df.SupportPerc.loc[index]
                        # delete if success support is higher
                        if s_support > f_support:
                            drop_list.append(index)

                f_df.drop(drop_list, inplace=True)
                
                print("Failed patterns length after eliminating patterns that have more support in success cases:", len(f_df))

                # Step 2: Delete patterns that are longer (length: n+1) than other patterns (length: n), with the same or less support

                drop_list = []

                # transform the pattern values to list
                f_df.Patterns = f_df.Patterns.str.split(" ")
                # get all the length values
                all_lens = pd.unique(f_df.Length)

                # iterate over patterns
                for ind, patt in enumerate(f_df.Patterns):
                # if patterns of length n+1 exists, get those patterns
                    if (len(patt)+1) in all_lens:
                        temp = f_df[f_df.Length == (len(patt)+1)]
                        # iterate over those patterns
                        for ind2, pat2 in enumerate(temp.Patterns):
                            # if the smaller pattern is a subset of larger pattern, check if the elements have the same order
                            if set(patt).issubset(set(pat2)):
                                orders = [pat2.index(o) for o in patt]
                                # to check for strictly increasing list
                                res = all(i < j for i, j in zip(orders, orders[1:]))
                                if res:
                                    if temp.Support.iloc[ind2] <= f_df.Support.iloc[ind]:
                                        drop_list.append(temp.index[ind2])

                f_df.drop(drop_list, inplace=True)

                print("Failed patterns length after eliminating weak extensions:", len(f_df))
                
                drop_list = []
                for ind, patt in f_df.iterrows():
                    if len(set(patt)) != len(patt):
                        drop_list.append(ind)

                f_df.drop(drop_list, inplace=True)

                # transform list to string
                f_df.Patterns = f_df.Patterns.apply(lambda x: " ".join(x))

                f_df = f_df.sort_values("Support", ascending=False)
                if writeFile:
                    f_df.to_csv("pruned_patts.csv")
                
                return f_df, f_df_before
            
def search(writeFile=False):
    """
    Automatically searches for patterns in downloaded range. Runs spade_mine function. If writeFile is True, the patterns are written to CSV files. Written to use in the Jenkins job.
    """
    # get BUILD_ID numbers in the dataframe
    builds = pd.read_csv("modified_dataframe.csv").BUILD_ID

    # get the range
    start_id = builds.min()
    end_id = builds.max()
    print("Search between", start_id, "and", end_id, "\n")
    
    # search for patterns
    patterns, before = spade_mine(start_id=start_id, end_id=end_id, minSup=0.15, maxSup=0.1)

    if patterns.empty:
        print("")
        print("No pattern detected for the support 0.15. Lowered to 0.1. \n")
        patterns, before = spade_mine(start_id=start_id, end_id=end_id, minSup=0.1, maxSup=0.1, writeFile=writeFile)

    return patterns, before

def analyze(pattern_row, df):
    """
    Performs a detailed analysis of a given pattern row, outputted by spade_mine or search. Written to use in a Jupyter notebook.
    """
    patt, supp, perc = pattern_row.Patterns, pattern_row.Support, str(pattern_row.SupportPerc *100)

    p_list = patt.split(" ")
    fail = p_list[-1]
    others = p_list[0:-1]

    if len(others) > 1:
        others = " and ".join(others)
    else:
        others = others[0]

    sliced = df.copy()

    for i in range(len(p_list)):
        if i != len(p_list) - 1:
            sliced = sliced[(sliced[p_list[i]] != "-") & (sliced[p_list[i+1]] != "-")]
            sliced = sliced[(sliced[p_list[i]].astype('int64') < sliced[p_list[i+1]].astype('int64'))]
        else:
            string = "F-" + str(p_list[i])
            found_f = sliced[sliced[string] == 1]
    
    print("Analysis for pattern:", (" ==> ").join(p_list))
    print("This pattern is observed", len(sliced), "times in all", len(df), "tests.", 100*len(sliced)/len(df), "%")
    print("The test", fail, "failed", len(found_f), "times in", len(sliced), "tests in which this pattern is observed.", 100*len(found_f)/len(sliced), "%")

    print("This pattern is observed", perc[0:5], "% of all failed test cases \n")
    
    print("Failed tests for this pattern:")
    print(count_fails(found_f))
    print("")
    print("Received error messages:")
    print(count_msg(found_f))

    fig = plt.figure(figsize=(10,3))
    fig.suptitle('Failed tests with this pattern', fontsize=16)
    plt.subplot(1,2,1)
    found_f.MERIDIO_VERSION.value_counts().plot(kind='bar')
    plt.ylabel("Number of failed tests")

    plt.subplot(1,2,2)
    found_f.TAPA_VERSION.value_counts().plot(kind='bar')
    plt.show()

    plt.figure(figsize=(10,3))
    plt.subplot(1,2,1)
    found_f.NSM_VERSION.value_counts().plot(kind='bar')
    plt.ylabel("Number of failed tests")

    plt.subplot(1,2,2)
    found_f.KUBERNETES_VERSION.value_counts().plot(kind='bar')
    plt.show()

    plt.figure(figsize=(5,3))
    found_f.IP_FAMILY.value_counts().plot(kind='bar')
    plt.ylabel("Number of failed tests")
    plt.show()

    found_f = found_f[found_f.columns[0:6]]
    return found_f