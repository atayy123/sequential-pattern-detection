import sys
import json
import os.path

# sample error messages
err_1="Internal error occurred: error executing command in container: failed to exec in container: failed to create exec"
err_2="All targets with the stream opened should have received traffic"
err_3="command terminated with exit code 137"
err_4="Timed out after"
err_5="Internal error occurred: error executing command in container: failed to exec in container: failed to load task"
err_6="command terminated with exit code 1; FAILED mapSharedData: tshm-stream-a-i"
err_7="unable to upgrade connection: container not found"
err_8="read: connection reset by peer - error from a previous attempt"
err_9="Internal error occurred: failed calling webhook"
err_10="command terminated with exit code 143"
err_11="Error from server (NotFound): pods"
err_12="No target should have received the traffic"
err_13="a vip cannot be shared between 2 conduits in this version"
err_14="unable to decode an event from the watch stream: http2: client connection lost"
err_15="error sending request"
err_16="a vip cannot be shared between 2 attractors in this version"
err_17="TLS handshake timeout"
err_18="Timeout occurred"
err_19="timed out waiting for the condition on pods"

def proc(parameter_file, json_file, csv_file):
    output = ""
    # create CSV format
    # MERIDIO_VERSION,TAPA_VERSION,BUILD_ID,NSM_VERSION,KUBERNETES_VERSION,IP_FAMILY,RESULT,SEQUENCE,FAILED,MESSAGE,TIME
    search = ['MERIDIO_VERSION=','TAPA_VERSION=','BUILD_ID=','NSM_VERSION=','KUBERNETES_VERSION=','IP_FAMILY=','RESULT=']
    
    # read the parameter file
    p_file = open(parameter_file, "r")
    
    # transform the lines to list
    lines = p_file.read().splitlines()
    p_file.close()
    
    # search the lines and extract parameters
    ind_search = 0
    while len(search) > ind_search:
        if search[ind_search] in lines[0]:
            output += lines[0].replace(search[ind_search],'') + ','
            ind_search += 1
        lines.pop(0)

    # read the JSON file
    j_file = open(json_file)
    j_data = json.load(j_file)
    j_file.close()
    
    # get the tests
    seq = ""
    fails = ""
    # create a list to save multiple error messages
    err_messages = []
    tests = j_data[0]["SpecReports"]
    for i in tests:
        test = i["ContainerHierarchyTexts"]
        if test != None:
            result = i["State"]

            if result != "skipped":
                seq = seq + test[1] + " "
        
            if result == "failed":
                # get the error message
                msg = i["Failure"]["Message"]
                # match with other error messages
                if err_1 in msg:
                    err_messages.append(err_1)
                elif err_2 in msg:
                    err_messages.append(err_2)
                elif err_3 in msg:
                    err_messages.append(err_3)
                elif err_4 in msg:
                    err_messages.append(err_4)
                elif err_5 in msg:
                    err_messages.append(err_5)
                elif err_6 in msg:
                    err_messages.append(err_6)
                elif err_7 in msg:
                    err_messages.append(err_7)
                elif err_8 in msg:
                    err_messages.append(err_8)
                elif err_9 in msg:
                    err_messages.append(err_9)
                elif err_10 in msg:
                    err_messages.append(err_10)
                elif err_11 in msg:
                    err_messages.append(err_11)
                elif err_12 in msg:
                    err_messages.append(err_12)
                elif err_13 in msg:
                    err_messages.append(err_13)
                elif err_14 in msg:
                    err_messages.append(err_14)
                elif err_15 in msg:
                    err_messages.append(err_15)
                elif err_16 in msg:
                    err_messages.append(err_16)
                elif err_17 in msg:
                    err_messages.append(err_17)
                elif err_18 in msg:
                    err_messages.append(err_18)
                elif err_19 in msg:
                    err_messages.append(err_19)
                
                # if error message is unknown, just replace the commas so that CSV works
                else:
                    err_messages.append(msg.replace(",",";"))
                
                fails = fails + test[1] + " "

    output += seq[0:-1] + ',' # dont save skipped tests!!!
    output += fails[0:-1] + ','
    # delete the same error messages from the list
    err_messages = list(dict.fromkeys(err_messages))
    # form one string from the list
    msg = "***".join(err_messages)

    output += msg + ',' # CSV format completed
    output += j_data[0]["StartTime"]

    # add CSV row to file
    if os.path.isfile(csv_file):
        f_csv = open(csv_file, "a")
    else:
        f_csv = open(csv_file, "a")
        f_csv.write("MERIDIO_VERSION,TAPA_VERSION,BUILD_ID,NSM_VERSION,KUBERNETES_VERSION,IP_FAMILY,RESULT,SEQUENCE,FAILED,MESSAGE,TIME")
    f_csv.write("\n" + output)
    f_csv.close()
    print("Writing to CSV is complete.")


if __name__ == "__main__":
    args = sys.argv
    parameter_file = args[1]
    json_file = args[2]
    csv_file = args[3]
    
    proc(parameter_file, json_file, csv_file)

