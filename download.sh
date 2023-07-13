mkdir data
mkdir data/folders
mkdir data/zipped

for i in $(seq $1 $2);
do
    echo Test Case: $i
    # download the data
    curl https://artifactory.nordix.org/artifactory/cloud-native/meridio/e2e-test-reports/$i.tar.gz --output data/zipped/$i.tar.gz

    # create directory for the zip contents
    mkdir data/folders/$i

    # extract zip
    tar -xzvf data/zipped/$i.tar.gz -C data/folders/$i/

    # check if file e2e_report.json exists in directory, then write to csv file
    if [ -f data/folders/$i/e2e_report.json ]; then python3 process.py data/folders/$i/parameters.txt data/folders/$i/e2e_report.json dataframe.csv ; else echo "E2E Report missing. Moving to next test run."; fi
done
