"""Synthetic fixtures for mechanical checks, not exam/source article samples."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from count_words import count
from audit_unit import audit


def base(mode, text='alpha beta gamma delta epsilon'):
    return {'unit_id':'synthetic-check','source_id':'synthetic-test-not-an-article',
            'mode':mode,'paragraphs':[{'id':'p1','text':text,'zh':'仅用于结构测试'}]}


def cloze():
    words=['alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota','kappa',
           'lambda','mu','nu','xi','omicron','pi','rho','sigma','tau','upsilon']
    text=' lead words '.join(words)
    u=base('cloze',text);u['gaps']=[];offset=0
    for n,word in enumerate(words,1):
        start=text.index(word,offset);offset=start+len(word)
        u['gaps'].append({'number':n,'start':start,'end':offset,'answer':word,
                          'options':{'A':word,'B':'alternative','C':'other','D':'different'},'correct':'A'})
    return u


def part_b(mode):
    u=base(mode);u['candidates']=[{'label':x,'text':'candidate '+x} for x in 'ABCDEFG']
    u['answers']=[{'number':41+i,'label':x} for i,x in enumerate('ABCDE')]
    u['targets']=[{'number':41+i,'description':'target '+str(i)} for i in range(5)]
    return u


def sorting():
    u=base('sorting');u['paragraphs']=[{'id':'p'+str(i),'text':'paragraph '+str(i),'zh':'测试'} for i in range(1,8)]
    u['candidates']=[{'label':c,'paragraph_id':'p'+str(i)} for i,c in enumerate('ABCDEFG',1)]
    u['answer_order']=list('ABCDEFG');u['fixed_positions']=[{'position':1,'label':'A'},{'position':7,'label':'G'}]
    u['answers']=[{'number':39+i,'position':i,'label':'ABCDEFG'[i-1]} for i in range(2,7)]
    return u


class AuditTests(unittest.TestCase):
    def assert_ok(self,u):
        result=audit(u);self.assertTrue(result['structural_ok'],result['errors']);return result
    def assert_bad(self,u):
        self.assertFalse(audit(u)['structural_ok'])
    def test_word_convention(self):
        x=count("Don't re-enter café’s naïve plans in 2027, 3.5 or 1,000.")
        self.assertEqual(x['core_english_words'],8)
        self.assertEqual(x['numeric_tokens_separate'],3)
    def test_decomposed_accents(self):
        self.assertEqual(count('cafe\u0301 déjà-vu')['core_english_words'],3)
    def test_cloze_20_and_local_gaps(self):
        r=self.assert_ok(cloze());self.assertEqual(len(r['adjacent_printed_word_gaps']),19)
        self.assertEqual(r['adjacent_printed_word_gaps'],[2]*19)
        self.assertIn('{{20}}',r['printed_text']);self.assertEqual(r['printed_count']['core_english_words'],38)
    def test_cloze_mismatched_answer(self):
        u=cloze();u['gaps'][0]['answer']='wrong';self.assert_bad(u)
    def test_cloze_overlap(self):
        u=cloze();u['gaps'][1]['start']=0;u['gaps'][1]['end']=5;self.assert_bad(u)
    def test_cloze_missing_item(self):
        u=cloze();u['gaps'].pop();self.assert_bad(u)
    def test_duplicate_options(self):
        u=cloze();u['gaps'][0]['options']['B']='alpha';self.assert_bad(u)
    def test_reading_numbering(self):
        u=base('reading_a');u['question_start']=26
        u['items']=[{'number':n,'stem':'Synthetic?','options':dict(A='one',B='two',C='three',D='four'),'correct':'B'} for n in range(26,31)]
        self.assert_ok(u);u['items'][-1]['number']=31;self.assert_bad(u)
    def test_e1_spans(self):
        u=base('translation_e1');text=u['paragraphs'][0]['text'];offset=0;u['spans']=[]
        for n,word in enumerate(text.split(),46):
            start=text.index(word,offset);offset=start+len(word)
            u['spans'].append(dict(number=n,start=start,end=offset,text=word,reference_translation='测试'))
        r=self.assert_ok(u);self.assertEqual(r['underlined_total_words'],5)
        u['spans'][0]['end']+=1;self.assert_bad(u)
    def test_e2_task(self):
        u=base('translation_e2');u.update(number=46,reference_translation='仅为测试译文');self.assert_ok(u)
        u['spans']=[{}];self.assert_bad(u)
    def test_matching_headings_and_reuse(self):
        for mode in ('matching','headings'):
            u=part_b(mode);self.assert_ok(u)
            u['answers'][1]['label']='A';self.assert_bad(u)
            u['allow_reuse']=True
            if mode=='matching':self.assert_ok(u)
            else:self.assert_bad(u)
    def test_insertion_restoration_and_load(self):
        u=part_b('insertion');text=u['paragraphs'][0]['text'];offset=0;u['gaps']=[]
        for i,word in enumerate(text.split()):
            start=text.index(word,offset);offset=start+len(word)
            u['gaps'].append(dict(number=41+i,start=start,end=offset));u['candidates'][i]['text']=word
        r=self.assert_ok(u);self.assertEqual(r['correct_fragment_words'],5)
        self.assertEqual(r['total_reading_load_words'],9)
        u['candidates'][0]['text']='not original';self.assert_bad(u)
    def test_sorting_restores_canonical_order(self):
        u=sorting();self.assert_ok(u)
        u['answer_order'][1:3]=['C','B'];self.assert_bad(u)
    def test_sorting_duplicate_positions(self):
        u=sorting();u['fixed_positions'][0]['position']=2;self.assert_bad(u)
    def test_unknown_candidate(self):
        u=part_b('headings');u['answers'][0]['label']='Z';self.assert_bad(u)
    def test_stale_body(self):
        u=base('translation_e2');u.update(number=46,reference_translation='测试',adapted_text='old text');self.assert_bad(u)
    def test_invalid_schema(self):
        for u in (None,[],{}, {'mode':'bad'}, {'mode':'cloze','paragraphs':[]}):self.assert_bad(u)
    def test_cli_exit_and_report(self):
        script=Path(__file__).resolve().parents[1]/'scripts/audit_unit.py'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'unit.json';out=Path(d)/'report.json';path.write_text(json.dumps(cloze()))
            result=subprocess.run([sys.executable,str(script),str(path),'--output',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(out.read_text())['structural_ok'])
            path.write_text('{}');result=subprocess.run([sys.executable,str(script),str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            path.write_text('{');result=subprocess.run([sys.executable,str(script),str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)


if __name__=='__main__':unittest.main()
