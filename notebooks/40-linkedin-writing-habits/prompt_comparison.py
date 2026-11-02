"""Paired article-level comparison of cached baseline and prompted generations."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import smoke_study as s

ROOT=Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
COMPARISON=ROOT/'data/prompt_comparison'
COMPARISON_SEED=20261102
COMPARISON_BOOTSTRAPS=2000
COMPARISON_MODELS=s.MODELS.copy()
TARGETS=['hashtag_tail','single_sentence_paragraphs','negative_contrast','clipped_rhythm',
         'additive_contrast','emoji_layout','bold_density','formulaic_framing','invented_experience','bold_leadins']
EXAMPLE_SLOTS=[('gpt-6.1-sol','14-seti',1),('gpt-6.1-sol','14-seti',2),
    ('claude-opus-5-5','14-seti',1),('gpt-6.1-terra','13-cursor-extension',1),
    ('claude-sonnet-5-5','06-protostar',5),('claude-sonnet-5-5','01-kimi',2)]


def paired_interval(values):
    vals=np.asarray(values,dtype=float)
    rng=np.random.default_rng(COMPARISON_SEED)
    if not len(vals):return None,None
    draws=vals[rng.integers(0,len(vals),(COMPARISON_BOOTSTRAPS,len(vals)))].mean(axis=1)
    return [float(v) for v in np.quantile(draws,[.025,.975])]


def compare_prompts():
    COMPARISON.mkdir(exist_ok=True)
    articles=s.load(ROOT/'data/main/articles.json');ids=[a['item_id'] for a in articles]
    classifier=s.load(ROOT/'data/decision_audit/protocol.json')
    assert classifier==s.load(ROOT/'data/plain_prose_v2/decisions/protocol.json')
    definitions=classifier['definitions'];conditions=[('baseline','main','decision_audit'),
        ('plain_prose_v2','plain_prose_v2','plain_prose_v2/decisions')]
    probability={};generation={};summary_by_condition={};record_by_condition={}
    usage_rows=[];reliability=[]
    for condition,folder,decision_folder in conditions:
        frame=pd.read_csv(ROOT/'data'/decision_folder/'classifications.csv')
        assert len(frame)==96000 and frame.valid.all(),condition
        assert not frame.duplicated(['post_id','zone','style_id']).any()
        probability[condition]={(r.writer_model,r.item_id,int(r.turn),r.zone,r.style_id):float(r.probability) for r in frame.itertuples()}
        records=[s.load(p) for p in sorted((ROOT/'data'/folder/'responses').glob('*/*/*.json')) if '.started.' not in p.name]
        assert len(records)==400 and all(r['status']=='ok' for r in records)
        record_by_condition[condition]=records
        generation[condition]={(r['requested_model'],r['item_id'],r['turn']):r for r in records}
        summary_by_condition[condition]=s.load(ROOT/'data'/folder/'summary.json')
        for modelrow in summary_by_condition[condition]['models']:
            usage_rows.append({'condition':condition,**modelrow})
        ds=s.load(ROOT/'data'/decision_folder/'summary.json')
        reliability.append({'condition':condition,**ds})
    expected=set(probability['baseline']);assert expected==set(probability['plain_prose_v2'])
    regions=classifier['zones'];pattern_rows=[];article_rows=[];overall_rows=[];turn_rows=[]
    for zone in regions:
        for style,definition in definitions.items():
            global_deltas=[];global_b=[];global_n=[]
            for model in COMPARISON_MODELS:
                b=np.array([[probability['baseline'][(model,item,t,zone,style)] for t in range(1,6)] for item in ids])
                n=np.array([[probability['plain_prose_v2'][(model,item,t,zone,style)] for t in range(1,6)] for item in ids])
                delta=100*((n>=.5).mean(axis=1)-(b>=.5).mean(axis=1))
                lo,hi=paired_interval(delta)
                row={'writer_model':model,'zone':zone,'style_id':style,'name':definition['name'],
                    'primary_target':style in TARGETS,'baseline_posts':100,'new_posts':100,
                    'baseline_present':int((b>=.5).sum()),'new_present':int((n>=.5).sum()),
                    'change_percentage_points':float(delta.mean()),'paired_article_95_low':lo,'paired_article_95_high':hi,
                    'baseline_high_confidence_present':int((b>=.8).sum()),'new_high_confidence_present':int((n>=.8).sum()),
                    'baseline_ambiguous':int(((b>.2)&(b<.8)).sum()),'new_ambiguous':int(((n>.2)&(n<.8)).sum()),
                    'baseline_mean_probability':float(b.mean()),'new_mean_probability':float(n.mean()),
                    'baseline_positive_topics':int(((b>=.5).sum(axis=1)>0).sum()),
                    'new_positive_topics':int(((n>=.5).sum(axis=1)>0).sum())}
                pattern_rows.append(row)
                for i,item in enumerate(ids):
                    article_rows.append({'writer_model':model,'item_id':item,'zone':zone,'style_id':style,
                        'baseline_present':int((b[i]>=.5).sum()),'new_present':int((n[i]>=.5).sum()),
                        'posts_per_condition':5,'change_percentage_points':float(delta[i])})
                global_deltas.append(delta);global_b.append(b);global_n.append(n)
                if zone=='whole':
                    for turn in range(5):
                        turn_rows.append({'writer_model':model,'turn':turn+1,'style_id':style,
                            'baseline_present':int((b[:,turn]>=.5).sum()),'new_present':int((n[:,turn]>=.5).sum()),'posts_per_condition':20})
            delta=np.mean(global_deltas,axis=0);lo,hi=paired_interval(delta)
            overall_rows.append({'zone':zone,'style_id':style,'name':definition['name'],'primary_target':style in TARGETS,
                'posts_per_condition':400,'baseline_present':int(sum((x>=.5).sum() for x in global_b)),
                'new_present':int(sum((x>=.5).sum() for x in global_n)),
                'change_percentage_points':float(delta.mean()),'paired_article_95_low':lo,'paired_article_95_high':hi,
                'baseline_high_confidence_present':int(sum((x>=.8).sum() for x in global_b)),
                'new_high_confidence_present':int(sum((x>=.8).sum() for x in global_n))})
    format_rows=[]
    for model in COMPARISON_MODELS:
        for feature in ['words','paragraphs','bold_spans','emoji_codepoints','hashtags','em_dashes','bullets','headings','closing_question']:
            b=np.array([[float(s.formatting(generation['baseline'][(model,item,t)]['text'])[feature]) for t in range(1,6)] for item in ids])
            n=np.array([[float(s.formatting(generation['plain_prose_v2'][(model,item,t)]['text'])[feature]) for t in range(1,6)] for item in ids])
            delta=(n-b).mean(axis=1);lo,hi=paired_interval(delta)
            format_rows.append({'writer_model':model,'feature':feature,'baseline_mean':float(b.mean()),'new_mean':float(n.mean()),
                'baseline_posts_containing':int((b>0).sum()),'new_posts_containing':int((n>0).sum()),
                'mean_change':float(delta.mean()),'paired_article_95_low':lo,'paired_article_95_high':hi})
    examples=[]
    by_id={x['item_id']:x for x in articles}
    for model,item,turn in EXAMPLE_SLOTS:
        row={'post_id':f'{item}/{model}/{turn:02d}','model':model,'item_id':item,'turn':turn,
             'source_title':by_id[item]['title'],'source_url':by_id[item]['url']}
        for condition in ['baseline','plain_prose_v2']:
            raw=generation[condition][(model,item,turn)];text=s.split_response(raw['text'])['body']
            row[condition]={'text':text,'zones':s.zones(raw['text']),'formatting':s.formatting(raw['text']),
                'probabilities':{style:probability[condition][(model,item,turn,'whole',style)] for style in definitions}}
        examples.append(row)
    family_rows=[]
    for family,members in [('OpenAI',COMPARISON_MODELS[:2]),('Anthropic',COMPARISON_MODELS[2:])]:
        for style in definitions:
            part=[r for r in pattern_rows if r['writer_model'] in members and r['zone']=='whole' and r['style_id']==style]
            family_rows.append({'family':family,'style_id':style,'member_1':members[0],'member_2':members[1],
                'member_1_baseline':part[0]['baseline_present'],'member_1_new':part[0]['new_present'],
                'member_2_baseline':part[1]['baseline_present'],'member_2_new':part[1]['new_present'],
                'baseline_present':sum(r['baseline_present'] for r in part),'new_present':sum(r['new_present'] for r in part),'posts_per_condition':200})
    for name,rows in [('patterns.csv',pattern_rows),('overall_patterns.csv',overall_rows),('paired_articles.csv',article_rows),
                      ('formatting.csv',format_rows),('usage.csv',usage_rows),('classifier_reliability.csv',reliability),
                      ('turns.csv',turn_rows),('families.csv',family_rows)]:s.write_csv(COMPARISON/name,rows)
    s.save(COMPARISON/'examples.json',examples)
    main=[r for r in overall_rows if r['zone']=='whole' and r['primary_target']]
    selected=[r for r in overall_rows if r['zone']=='whole']
    old_sessions={r['session_id'] for r in record_by_condition['baseline']}
    new_sessions={r['session_id'] for r in record_by_condition['plain_prose_v2']}
    assert not old_sessions&new_sessions,'Conditions reused conversation history'
    result={'conditions':2,'posts_per_condition':400,'writers':4,'articles':20,'turns':5,
        'primary_targets':main,'all_whole_post_patterns':selected,
        'new_writer_readable':400,'fresh_conversation_ids':not bool(old_sessions&new_sessions),
        'classifier_definitions_identical':True,'comparison_unit':'paired article, keeping all writers and five turns together',
        'bootstrap_draws':COMPARISON_BOOTSTRAPS,'human_quality_validated':False,
        'condition_classifier_summaries':reliability,
        'scope':'Exploratory intervention; baseline earlier in time, undated writer IDs, classifier labels not reader preference.'}
    s.save(COMPARISON/'summary.json',result)
    print(json.dumps({'primary_targets':main,'formatting':format_rows},indent=2))
    return result


if __name__=='__main__':compare_prompts()
