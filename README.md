# Parallelizing operations on SAM/BAM files

SAM/BAM files are typically large, thus, operations on these files are time intensive. This project provides tools to parallelize operations on SAM/BAM files. The workflow follows:

1. Split BAM/SAM file in _n_ chunks
2. Perform operation in each chunk in a dedicated process and save resulting SAM/BAM chunk 
3. Merge results back into a single SAM/BAM file

Depends on:

1. Samtools

# Installation

```pip3 install parallelbam```

or

1. Git clone project
2. cd to cloned project directory
3. ```sudo python3 setup.py install```

Better to install within an environment, such as a conda environment, to avoid
path conflicts with the included bash scripts.

# Usage

There is one main function named ```parallelizedBAMoperation```. This function takes as mandatory arguments:

1. path to original bam file (should be ordered)
2. a callable function to perform the operation on each bam file chunk

The callable function must accept the following two first arguments: 

1. path to input bam file and
2. path to resulting output bam file

in this order.

# TODO

1. The current way to include bash scripts in the package, while working, seems awkward. Perhaps including bash code directly in subprocess would be simpler
2. Having permission error in some installations upon calling splitBAM.sh, can one make it executable during installation?


```python
from parallelbam.parallelbam import parallelizeBAMoperation, getNumberOfReads
```

As an example, let's create a function that simply copies a bam file to another directory (does nothing to the bam file). When calling this function in ```parallelizeBAMoperation``` it will imply split the BAM file in chunks and the merge them back into a single BAM, whih sould be identical to the first one. We will split the BAM file in 8 chunks, and are dummy function will be called in separate process for each chunk.


```python
import shutil

def foo(input_bam, output_bam):
    shutil.copyfile(input_bam, output_bam)
    
    
parallelizeBAMoperation('sample.bam',
                        foo, output_dir=None,
                        n_processes=8)
```

To check that the processed bam file, after merging the 8 chunks, contains the same number of reads we can call ```getNumberOfReads```.


```python
getNumberOfReads('sample.bam')
```




    11825588




```python
getNumberOfReads('processed.bam')
```




    11825588


