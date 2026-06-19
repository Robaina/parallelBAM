"""Shared fixtures and helpers for the parallelBAM test battery."""
import os
import shutil
import subprocess

import pytest

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TOY_BAM = os.path.join(DATA_DIR, "toy_sample.bam")
TOY_SAM = os.path.join(DATA_DIR, "toy_sample.sam")

# Number of reads in the bundled toy sample (verified with `samtools view -c`).
TOY_N_READS = 1000


def samtools_on_path() -> bool:
    return shutil.which("samtools") is not None


def count_reads(path_to_bam: str) -> int:
    """Independent read count via samtools, used to assert against the package."""
    out = subprocess.run(
        ["samtools", "view", "-c", path_to_bam],
        stdout=subprocess.PIPE,
        check=True,
    )
    return int(out.stdout.decode("utf-8").strip())


def has_header(path_to_bam: str) -> bool:
    """True if the BAM carries at least one header line."""
    out = subprocess.run(
        ["samtools", "view", "-H", path_to_bam],
        stdout=subprocess.PIPE,
        check=True,
    )
    return len(out.stdout.decode("utf-8").strip()) > 0


# Skip the whole suite gracefully if samtools is unavailable rather than
# erroring out with cryptic subprocess failures.
pytestmark = pytest.mark.skipif(
    not samtools_on_path(), reason="samtools not found on PATH"
)


@pytest.fixture(autouse=True)
def _require_samtools():
    if not samtools_on_path():
        pytest.skip("samtools not found on PATH")


@pytest.fixture
def sample_bam(tmp_path):
    """A fresh, isolated copy of the toy BAM in a writable temp directory.

    The package writes chunk directories and a default ``processed.bam`` next to
    the input file, so each test gets its own copy to avoid cross-talk.
    """
    dest = tmp_path / "sample.bam"
    shutil.copyfile(TOY_BAM, dest)
    return dest
