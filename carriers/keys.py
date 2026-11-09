"""Parse VAT/VCF/comparison keys without claiming biological normalization.
Inputs: key strings supplied by callers; outputs: coordinate/allele tuples or strings.
Decision: remove file prefixes and a single chr prefix; preserve alleles exactly.
No reference lookup, genome-build conversion, indel left alignment, or data I/O.
"""
import re

def _validate(chrom, pos, ref, alt):
    chrom = str(chrom).removeprefix('chr')
    if not chrom or int(pos) < 1 or not re.fullmatch('[ACGTN]+', ref) or not re.fullmatch('[ACGTN]+', alt):
        raise ValueError('Expected a positive position and sequence alleles')
    return chrom, int(pos), ref, alt

def vat_to_vcf(vid):
    c,p,r,a = _validate(*vid.split('-',3))
    return 'chr'+c,p,r,a

def vcf_to_vat(chrom, pos, ref, alt):
    c,p,r,a = _validate(chrom,pos,ref,alt)
    return f'{c}-{p}-{r}-{a}'

def comparison_key_to_vat(key):
    # The rightmost four components discard arbitrary path / .vcf prefixes.
    parts = key.rsplit(':',4)[-4:]
    if len(parts) != 4:
        return vcf_to_vat(*vat_to_vcf(key))
    return vcf_to_vat(*parts)

def canonical_key(key):
    c,p,r,a = vat_to_vcf(comparison_key_to_vat(key))
    return f'{c}:{p}:{r}:{a}'
