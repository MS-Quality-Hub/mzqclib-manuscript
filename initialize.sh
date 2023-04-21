#!/bin/sh
echo "Downloading file to test_data/"
mkdir -p test_data
cd test_data
wget -O 20181113_010_autoQC01.raw "https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?file=f.MSV000086542/raw/20181113_010_autoQC01.raw&forceDownload=true"
if test $? -eq 0 
then
    cd ..
    echo "Building thermorawfileparser singularity container"
    cd container/thermorawfileparser/
    rm *.simg
    ./create-simg.sh
    cd ../../
else
    echo "Downloading test file failed with code= $?"
    exit 1
fi
