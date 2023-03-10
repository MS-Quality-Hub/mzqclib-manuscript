#!/bin/bash
java -jar /opt/jmzqc_usecase/target/jmzqc-usecase-1.0.0-SNAPSHOT-cli.jar "$@" &> error.log || true
eval=$(sed -n 'x;$p' error.log)
exp2last="Validation successful!"
if [[ "${eval}" == "${exp2last}"  ]]
then 
	echo "success"
	exit 0; 
else 
	echo "fail"
	exit 2;
fi
