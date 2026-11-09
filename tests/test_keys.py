# All keys below are fabricated syntax examples, not observed variants.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "carriers"))
from keys import comparison_key_to_vat, vat_to_vcf, vcf_to_vat  # noqa: E402


def test_vat_roundtrip():
    assert vat_to_vcf("13-101-GT-G") == ("chr13", 101, "GT", "G")
    assert vcf_to_vat("chr13", 101, "GT", "G") == "13-101-GT-G"


def test_comparison_key_with_path_prefix():
    k = "synthetic/path/acmg_chr10.vcf:chr10:202:C:CA"
    assert comparison_key_to_vat(k) == "10-202-C-CA"


def test_long_insertion():
    k = "x/acmg_chr2.vcf:chr2:303:T:TTCAAAAGGGACATAGAAAA"
    assert comparison_key_to_vat(k) == "2-303-T-TTCAAAAGGGACATAGAAAA"
