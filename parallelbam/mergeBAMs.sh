#!/usr/bin/env bash

# Merge BAM files in directory
# Arguments:
# $1: path to bam files directory

cd $1
samtools merge merged.bam *.bam