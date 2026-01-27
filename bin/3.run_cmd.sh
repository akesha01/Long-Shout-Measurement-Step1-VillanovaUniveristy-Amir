#!/bin/bash

CMD="save_iq_w_tx_cw"
BASEOUTDIR="/local/data/"
REPODIR="/local/repository"
CMDDIR="${REPODIR}/etc/cmdfiles"

# Change this if you are not running this script on the orchestrator node.
ORCHNODE=localhost

outdir="${BASEOUTDIR}/Shout_meas_"$(date +"%m-%d-%Y_%H-%M-%S")
mkdir -p $outdir

cmd_file="${CMDDIR}/${CMD}.json"
cp  $cmd_file "${outdir}/${CMD}.json"

cd "${REPODIR}/shout"
python3 measiface.py -l "${outdir}/log" -o "${outdir}/" -s $ORCHNODE -c $cmd_file
