import os
import shutil
import math
import subprocess
from multiprocessing import Process
import string
import random

def getRandomString(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def getNumberOfReads(path_to_bam: str) -> int:
    """
    Return number of reads in bam file
    """
    return int(
        subprocess.run(
            [f'samtools view -c {path_to_bam}'],
            shell=True,
            stdout=subprocess.PIPE
        ).stdout.decode('utf-8').replace('\n', '')
    )
    
def splitBAM(path_to_bam: str, n_parts: int) -> None:
    """
    Split BAM file into N parts of roughly equal size
    """
    path_to_bam = os.path.abspath(path_to_bam)
    bam_dir = os.path.dirname(path_to_bam)
    bam_file = os.path.basename(path_to_bam)
    
    n_reads = getNumberOfReads(path_to_bam)
    part_size = math.ceil(n_reads / n_parts) + 1
    
    subprocess.run(
        ['../../../../bin/splitBAM.sh',
         bam_dir,
         bam_file,
         str(part_size)]
    )
    
def mergeBAMs(bam_files_dir: str, output_dir: str) -> None:
    """
    Merge bam files into a single bam
    """
    subprocess.run(
        ['../../../../bin/mergeBAMs.sh',
         bam_files_dir]
    )
    
    os.rename(os.path.join(bam_files_dir, 'merged.bam'), output_dir)

def parallelizeBAMoperation(path_to_bam: str,
                            callback, callback_additional_args: list = [], 
                            output_dir: str = None,
                            n_processes: int = 2) -> None:
    """
    Parallelize operation on a large BAM
    
    This function splits the BAM file into as many chunks as the provided number of
    processes, calls function on a separate process for each chunk and then merges
    the outputs into a single (result) BAM file.
    
    callback: python function object. The first two arguments must be the path to
    the input BAM and the path to the ouput (processed) bam file.
    
    callback_additional_args: List containing additional arguments to callback, the 
    first argument must be left for the str containing the path to the BAM file
    
    """
    path_to_bam = os.path.abspath(path_to_bam)
    bam_dir = os.path.dirname(path_to_bam)
    chunks_dir = os.path.join(bam_dir, 'temp_BAM_chunks')
    processed_chunks_dir = os.path.join(bam_dir, f'temp_processed_chunks{getRandomString()}')
    os.mkdir(processed_chunks_dir)
    if output_dir is None:
        output_dir = os.path.join(bam_dir, 'processed.bam')
    
    splitBAM(path_to_bam, n_parts=n_processes)
    
    processes = []
    for n in range(n_processes):
        
        p_input_dir = os.path.join(chunks_dir, f'{n + 1}.bam')
        p_output_dir = os.path.join(processed_chunks_dir, f'out{n + 1}.bam')
        
        cb_args = tuple([p_input_dir, p_output_dir] + callback_additional_args)
        processes.append(
            Process(target=callback, args=cb_args)
        )
        processes[-1].start()
        processes[-1].join()

    mergeBAMs(processed_chunks_dir, output_dir)
    
    shutil.rmtree(processed_chunks_dir, ignore_errors=True)
    shutil.rmtree(chunks_dir, ignore_errors=True)    