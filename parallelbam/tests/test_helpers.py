"""Tests for the small helper utilities: getRandomString and getNumberOfReads."""
import string

import pytest

from parallelbam.parallelbam import getRandomString, getNumberOfReads

from conftest import TOY_BAM, TOY_N_READS


class TestGetRandomString:
    def test_default_length(self):
        assert len(getRandomString()) == 6

    @pytest.mark.parametrize("size", [1, 4, 12, 32])
    def test_custom_length(self, size):
        assert len(getRandomString(size=size)) == size

    def test_uses_expected_charset(self):
        allowed = set(string.ascii_uppercase + string.digits)
        s = getRandomString(size=200)
        assert set(s).issubset(allowed)

    def test_respects_custom_charset(self):
        s = getRandomString(size=50, chars="ab")
        assert set(s).issubset({"a", "b"})

    def test_values_vary(self):
        # Astronomically unlikely to collide across many draws of length 6.
        values = {getRandomString() for _ in range(50)}
        assert len(values) > 1


class TestGetNumberOfReads:
    def test_counts_toy_sample(self):
        assert getNumberOfReads(TOY_BAM) == TOY_N_READS

    def test_returns_int(self):
        assert isinstance(getNumberOfReads(TOY_BAM), int)
