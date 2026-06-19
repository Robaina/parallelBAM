"""Tests for splitBAM and mergeBAMs."""
import os

import pytest

from parallelbam.parallelbam import splitBAM, mergeBAMs, getNumberOfReads

from conftest import TOY_N_READS, count_reads, has_header


def _chunk_dir(bam_path):
    return os.path.join(os.path.dirname(str(bam_path)), "temp_BAM_chunks")


class TestSplitBAM:
    @pytest.mark.parametrize("n_parts", [1, 2, 4, 8])
    @pytest.mark.parametrize("sort_by_name", [True, False])
    def test_produces_expected_number_of_chunks(self, sample_bam, n_parts, sort_by_name):
        splitBAM(str(sample_bam), n_parts=n_parts, sort_by_name=sort_by_name)
        chunks = os.listdir(_chunk_dir(sample_bam))
        assert len(chunks) == n_parts

    @pytest.mark.parametrize("n_parts", [1, 2, 4, 8])
    @pytest.mark.parametrize("sort_by_name", [True, False])
    def test_preserves_total_read_count(self, sample_bam, n_parts, sort_by_name):
        splitBAM(str(sample_bam), n_parts=n_parts, sort_by_name=sort_by_name)
        cdir = _chunk_dir(sample_bam)
        total = sum(count_reads(os.path.join(cdir, c)) for c in os.listdir(cdir))
        assert total == TOY_N_READS

    def test_every_chunk_carries_a_header(self, sample_bam):
        splitBAM(str(sample_bam), n_parts=4)
        cdir = _chunk_dir(sample_bam)
        for chunk in os.listdir(cdir):
            assert has_header(os.path.join(cdir, chunk))

    def test_chunks_named_sequentially_from_one(self, sample_bam):
        splitBAM(str(sample_bam), n_parts=4)
        names = sorted(os.listdir(_chunk_dir(sample_bam)))
        assert names == ["1.bam", "2.bam", "3.bam", "4.bam"]

    def test_accepts_relative_path(self, sample_bam, monkeypatch):
        # splitBAM abspaths the input internally; ensure a relative path works.
        monkeypatch.chdir(sample_bam.parent)
        splitBAM(sample_bam.name, n_parts=2)
        assert len(os.listdir(_chunk_dir(sample_bam))) == 2

    def test_multiple_threads_path(self, sample_bam):
        # n_threads is forwarded to the samtools name-sort; result must be unchanged.
        splitBAM(str(sample_bam), n_parts=2, sort_by_name=True, n_threads=2)
        cdir = _chunk_dir(sample_bam)
        total = sum(count_reads(os.path.join(cdir, c)) for c in os.listdir(cdir))
        assert total == TOY_N_READS


class TestMergeBAMs:
    def test_merge_reconstitutes_read_count(self, sample_bam, tmp_path):
        splitBAM(str(sample_bam), n_parts=4)
        cdir = _chunk_dir(sample_bam)
        out = tmp_path / "merged_out.bam"
        mergeBAMs(cdir, str(out))
        assert out.exists()
        assert getNumberOfReads(str(out)) == TOY_N_READS

    def test_merge_renames_to_requested_output(self, sample_bam, tmp_path):
        splitBAM(str(sample_bam), n_parts=2)
        cdir = _chunk_dir(sample_bam)
        out = tmp_path / "custom_name.bam"
        mergeBAMs(cdir, str(out))
        # The intermediate merged.bam should have been renamed away.
        assert not os.path.exists(os.path.join(cdir, "merged.bam"))
        assert out.exists()
