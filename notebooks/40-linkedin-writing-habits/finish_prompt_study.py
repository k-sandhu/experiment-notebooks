"""Explicit full-run driver; ordinary notebook execution never imports this script."""
import prompt_study as p
import prompt_comparison as c

if __name__=='__main__':
    p.collect_prompt_study(max_new=360)
    records=p.intervention_records()
    assert len(records)==400 and all(r['status']=='ok' for r in records),'Reconcile incomplete writer collection before classifying'
    p.classify_prompt_study(posts=400,max_new=796)
    p.analyse_prompt_study()
    c.compare_prompts()
