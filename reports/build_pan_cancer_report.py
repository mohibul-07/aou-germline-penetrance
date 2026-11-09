"""Adapt the actual pan_cancer_research_report.html builder for code-only export.
Inputs: REPORT_DATA JSON, REPORT_TEXT JSON slot->reviewed plain text,
REPORT_OCT7_FRAGMENT external reviewed HTML (may be empty); output REPORT_HTML.
Decisions: preserve original interactive charts; no embedded result payloads in
source. Output remains internal and needs disclosure review, including text and
fragment, before sharing. Historical report statements are not current findings.
"""
import json,re,html
from workflow.runtime import external
from reports.pan_cancer_template import TEMPLATE

def main():
    data=json.loads(external('REPORT_DATA').read_text())
    for row in data['phenotypes']:
        if row['broad']-row['malignant']!=row['broad_only'] or not row['malignant_ge2']<=row['malignant']<=row['broad']:
            raise ValueError('Phenotype identities failed')
    c=data['cohort']
    if c['with_phecodes']+c['without_phecodes']!=c['wgs']: raise ValueError('Roster identity failed')
    v=data['variant_comparison']
    if v['both']+v['clinvar_only']!=v['clinvar'] or v['both']+v['fastvep_only']!=v['fastvep']:
        raise ValueError('Historical variant identities failed')
    narrative=json.loads(external('REPORT_TEXT').read_text())
    result=TEMPLATE
    for slot in set(re.findall(r'__TEXT_\d+__',result)):
        if slot not in narrative: raise ValueError('Missing external report narrative slot')
        result=result.replace(slot,html.escape(narrative[slot]))
    result=result.replace('__OCT7__',external('REPORT_OCT7_FRAGMENT').read_text())
    result=result.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c'))
    external('REPORT_HTML',True).write_text(result)

if __name__=='__main__': main()
