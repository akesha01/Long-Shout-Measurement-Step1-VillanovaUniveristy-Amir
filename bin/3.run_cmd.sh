#!/bin/bash

CMDDIR="/local/repository/etc/cmdfiles"
OUT="/local/data/"
mkdir -p $OUT

cd /local/repository/
#git submodule update --init --remote || { echo "Failed to update git submodules!" && exit 1; }

START=1
REPEAT=1
for i in $(eval echo "{$START..$REPEAT}")
do
	#for CMD in "save_iq_w_simult_tx_1" "save_iq_w_simult_tx_2" "save_iq_w_simult_tx_3"
	#for CMD in "save_iq_w_simult_tx_2" "save_iq_w_simult_tx_3"
	for CMD in "save_iq_w_tx_file"
	do
	
		today=$(date +"%m-%d-%Y")
		now=$(date +"%H-%M-%S")
		out="$OUT"/Shout_meas_"$today"_"$now"
		mkdir "$out"

		cmd_file="$CMDDIR/$CMD.json"
		cp  $cmd_file "$out/$CMD.json"

		cd /local/repository/shout
		python3 measiface.py -l "$out/log" -o "$out/" -c $cmd_file

	done

done