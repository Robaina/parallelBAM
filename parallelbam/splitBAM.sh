#!/usr/bin/env bash

# Split large BAM file into chunks of given maximum size
# bash splitBAM.sh workdir input.bam n_reads_in_chunk [sort_by_name] [threads]

# Based on https://bioinformatics.stackexchange.com/questions/7052/chunk-alignment-in-a-name-sorted-bam-for-parallel-processing

# Arguments:
# $1: path to working directory
# $2: path to bam file
# $3: number of reads in each chunk
# $4: sort reads by name before splitting (1=yes, 0=no). Default 1.
#     Name-sorting keeps reads sharing a query name (e.g. mates) within the
#     same chunk, but requires a full serial sort of the whole file. Set to 0
#     for order-independent, per-read operations to skip it (much faster).
# $5: number of threads for the samtools name-sort. Default 1.

cd $1
mkdir -p temp_BAM_chunks

sort_by_name=${4:-1}
threads=${5:-1}

if [ "$sort_by_name" -eq 1 ]; then
    # Write samtools sort spill files under temp_BAM_chunks/ (via -T) so that,
    # if the sort is interrupted (e.g. the downstream pipe closes early or the
    # job is killed), the orphaned tmp.*.bam files land in the temp directory
    # that the caller removes afterwards, instead of the output directory.
    reader=(samtools sort -n -@ "$threads" -T "temp_BAM_chunks/samtools_sort" -O SAM "$2")
else
    reader=(samtools view -h "$2")
fi

"${reader[@]}"|awk -v n=$3 -v FS="\t" '
BEGIN { part=0; line=n }
/^@/ {header = header$0"\n"; next;}
{ if( line>=n && $1!=last_read ) {part++; line=1;}
  print line==1 ? header""$0 : $0 | "samtools view -b -o temp_BAM_chunks/"part".bam"
  last_read = $1;
  line++;
}'
