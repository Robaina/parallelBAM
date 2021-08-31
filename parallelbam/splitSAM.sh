#!/usr/bin/env bash

# Split large SAM file into chunks of given maximum size
# bash splitSAM.sh input.bam n_reads_in_chunk

# Taken from https://bioinformatics.stackexchange.com/questions/7052/chunk-alignment-in-a-name-sorted-bam-for-parallel-processing

# Arguments:
# $1: path to working directory
# $2: path to bam file
# $3: number of reads in each chunk

cd $1
mkdir -p temp_SAM_chunks

samtools sort -n -O SAM $2|awk -v n=$3 -v FS="\t" '
  BEGIN { part=0; line=n }       
  /^@/ {header = header$0"\n"; next;} 
  { if( line>=n && $1!=last_read ) {part++; line=1; printf header > "temp_SAM_chunks/"part".sam"; } 
    else { line++; } 
    last_read = $1;
  }'