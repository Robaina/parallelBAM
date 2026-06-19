"""Tests for the main entry point: parallelizeBAMoperation."""
import os
import shutil
import subprocess

import pytest

from parallelbam.parallelbam import parallelizeBAMoperation, getNumberOfReads

from conftest import TOY_BAM, TOY_N_READS, count_reads


# Callbacks are defined at module level so they remain importable/picklable
# regardless of the multiprocessing start method.
def copy_callback(input_bam, output_bam):
    """No-op operation: just copy the chunk through unchanged."""
    shutil.copyfile(input_bam, output_bam)


def flag_filter_callback(input_bam, output_bam, include_flag):
    """Keep only reads carrying a given SAM flag bit (a per-read operation)."""
    subprocess.run(
        ["samtools", "view", "-b", "-f", str(include_flag), "-o", output_bam, input_bam],
        check=True,
    )


def _temp_artifacts(directory):
    return [d for d in os.listdir(directory) if d.startswith("temp_")]


class TestParallelizeIdentity:
    @pytest.mark.parametrize("n_processes", [2, 4])
    @pytest.mark.parametrize("sort_by_name", [True, False])
    def test_read_count_preserved(self, sample_bam, tmp_path, n_processes, sort_by_name):
        out = tmp_path / "processed.bam"
        parallelizeBAMoperation(
            str(sample_bam),
            copy_callback,
            output_path=str(out),
            n_processes=n_processes,
            sort_by_name=sort_by_name,
        )
        assert out.exists()
        assert getNumberOfReads(str(out)) == TOY_N_READS

    def test_default_output_path(self, sample_bam):
        # output_path=None writes processed.bam next to the input BAM.
        parallelizeBAMoperation(
            str(sample_bam), copy_callback, output_path=None, n_processes=2
        )
        default_out = sample_bam.parent / "processed.bam"
        assert default_out.exists()
        assert getNumberOfReads(str(default_out)) == TOY_N_READS

    def test_temp_directories_cleaned_up(self, sample_bam, tmp_path):
        out = tmp_path / "processed.bam"
        parallelizeBAMoperation(
            str(sample_bam), copy_callback, output_path=str(out), n_processes=4
        )
        # Neither the chunk dir nor the processed-chunk dir should survive.
        assert _temp_artifacts(sample_bam.parent) == []


class TestParallelizeWithProcessing:
    # 0x40 == first-in-pair; a per-read flag that splits the toy sample.
    INCLUDE_FLAG = 0x40

    def test_additional_args_forwarded_and_applied(self, sample_bam, tmp_path):
        expected = count_reads_with_flag(TOY_BAM, self.INCLUDE_FLAG)

        out = tmp_path / "filtered.bam"
        parallelizeBAMoperation(
            str(sample_bam),
            flag_filter_callback,
            callback_additional_args=[self.INCLUDE_FLAG],
            output_path=str(out),
            n_processes=4,
            sort_by_name=False,
        )
        assert out.exists()
        # Per-read filtering is order-independent: chunked result == whole-file result.
        assert getNumberOfReads(str(out)) == expected

    def test_filtering_actually_removes_reads(self):
        # Sanity guard: the filter must drop some (but not all) reads, otherwise
        # the previous test could pass trivially.
        kept = count_reads_with_flag(TOY_BAM, self.INCLUDE_FLAG)
        assert 0 < kept < TOY_N_READS


def count_reads_with_flag(path_to_bam, include_flag):
    out = subprocess.run(
        ["samtools", "view", "-c", "-f", str(include_flag), path_to_bam],
        stdout=subprocess.PIPE,
        check=True,
    )
    return int(out.stdout.decode("utf-8").strip())
