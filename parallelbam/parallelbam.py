import os
from pathlib import Path
import shutil
import math
import subprocess
from multiprocessing import Process
import string
import random

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
path_to_bash_scripts = str(Path(dir_path).parents[3])
splitBAM_file = os.path.join(path_to_bash_scripts, "bin", "splitBAM.sh")
if not os.path.exists(splitBAM_file):
    path_to_bash_scripts = str(Path(dir_path).parents[4])
# Make bash scripts executable
subprocess.run(
[f'chmod +x {os.path.join(path_to_bash_scripts, "bin", "splitBAM.sh")}'],
shell=True
)
subprocess.run(
[f'chmod +x {os.path.join(path_to_bash_scripts, "bin", "mergeBAMs.sh")}'],
shell=True
)

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
    
def splitBAM(path_to_bam: str, n_parts: int,
             sort_by_name: bool = True, n_threads: int = 1) -> None:
    """
    Split BAM file into N parts of roughly equal size

    sort_by_name: if True (default), reads are name-sorted before splitting so
    that reads sharing a query name (e.g. mates) stay within the same chunk.
    This requires a full serial sort of the whole file. Set to False for
    order-independent, per-read operations to skip the sort (much faster).

    n_threads: number of threads passed to the samtools name-sort.
    """
    path_to_bam = os.path.abspath(path_to_bam)
    bam_dir = os.path.dirname(path_to_bam)
    bam_file = os.path.basename(path_to_bam)

    n_reads = getNumberOfReads(path_to_bam)
    part_size = math.ceil(n_reads / n_parts) + 1

    subprocess.run(
        [os.path.join(path_to_bash_scripts, 'bin', 'splitBAM.sh'),
         bam_dir,
         bam_file,
         str(part_size),
         '1' if sort_by_name else '0',
         str(n_threads)]
    )
    
def mergeBAMs(bam_files_dir: str, output_path: str) -> None:
    """
    Merge bam files into a single bam
    """
    subprocess.run(
        [os.path.join(path_to_bash_scripts, 'bin', 'mergeBAMs.sh'),
         bam_files_dir]
    )
    os.rename(os.path.join(bam_files_dir, 'merged.bam'), output_path)

def parallelizeBAMoperation(path_to_bam: str,
                            callback, callback_additional_args: list = [],
                            output_path: str = None,
                            n_processes: int = 2,
                            sort_by_name: bool = True) -> None:
    """
    Parallelize operation on a large BAM

    This function splits the BAM file into as many chunks as the provided number of
    processes, calls function on a separate process for each chunk and then merges
    the outputs into a single (result) BAM file.

    callback: python function object. The first two arguments must be the path to
    the input BAM and the path to the ouput (processed) bam file.

    callback_additional_args: List containing additional arguments to callback, the
    first argument must be left for the str containing the path to the BAM file

    sort_by_name: if True (default), the BAM is name-sorted before splitting so
    that reads sharing a query name (e.g. mates) stay within the same chunk. This
    is a full serial sort of the whole file and is often the dominant cost. Set to
    False when the callback operates on each read independently (e.g. filtering by
    per-read identity) to skip the sort and split the file as-is, which is much
    faster on large inputs.

    """
    path_to_bam = os.path.abspath(path_to_bam)
    bam_dir = os.path.dirname(path_to_bam)
    chunks_dir = os.path.join(bam_dir, 'temp_BAM_chunks')
    processed_chunks_dir = os.path.join(bam_dir, f'temp_processed_chunks{getRandomString()}')
    os.mkdir(processed_chunks_dir)
    if output_path is None:
        output_path = os.path.join(bam_dir, 'processed.bam')
    
    splitBAM(path_to_bam, n_parts=n_processes,
             sort_by_name=sort_by_name, n_threads=n_processes)
    
    processes = []
    for n in range(n_processes):
        p_input_path = os.path.join(chunks_dir, f'{n + 1}.bam')
        p_output_path = os.path.join(processed_chunks_dir, f'out{n + 1}.bam')
        
        cb_args = tuple([p_input_path, p_output_path] + callback_additional_args)
        processes.append(
            Process(target=callback, args=cb_args)
        )
    for p in processes:
        p.start()   
    for p in processes:
        p.join()
   
    mergeBAMs(processed_chunks_dir, output_path)
    
    shutil.rmtree(processed_chunks_dir, ignore_errors=True)
    shutil.rmtree(chunks_dir, ignore_errors=True)