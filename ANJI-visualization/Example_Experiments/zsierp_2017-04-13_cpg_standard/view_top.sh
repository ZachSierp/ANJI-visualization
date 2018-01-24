#!/bin/bash
BASE_DIR=$( pwd )
JOB_CSV="$BASE_DIR/PARAMETERS/parameter_list.csv"

REPORT_CSV="$BASE_DIR/job_report.csv"
cd DATA_DIR
echo "job,fit,cmplx,gens,parameters*" > $REPORT_CSV

for job in $( ls  ); 
do

  PERF=$( xmllint --xpath '//generation[last()]//max' $BASE_DIR/DATA_DIR/$job/run/run0.xml | sed "s/<max>/fitness: /" | sed "s/<max>/ complexity: /" | sed "s/<\/max>//g" | awk '{printf($2 ", "$4 )}' )
  GENERATION=$( cat $BASE_DIR/DATA_DIR/$job/run/run0.xml |grep "generation id=" | sed -E "s/(.*generation id=\")(.*)/\2 \1/" | sed -E "s/([^\"]*)\".*/\1/" | sort -n | tail -1   )
  echo -n "$job,$PERF,$GENERATION" >> $REPORT_CSV
  
  for label in $( cat $JOB_CSV  | sed "s/.*,//" );
  do
    value=$(cat $BASE_DIR/JOBS_DIR/$job.properties | grep "$label" | grep -v "#" | sed "s/.*=//" )

    if [ -n "$value" ]; then
    	#can be commented out, just for debug
    	#echo -n " [ $label ] = [ $value ]"
    	#echo " --------- "
	    echo -n  ",$label=$value" >> $REPORT_CSV
    fi
  done
  
  echo "" >> $REPORT_CSV
done

cd ..

cat $REPORT_CSV > temp

for line in $(cat $JOB_CSV | sed "s/,.*,/=/")
do
	array=(${line//=/ })
	search="${array[1]}"
	replace="${array[0]}"
	cat temp | sed "s/$search/$replace/" > $REPORT_CSV
	cat $REPORT_CSV > temp
done

rm temp
