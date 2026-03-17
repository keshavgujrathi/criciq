run:
	streamlit run app.py

eval:
	python -c "from eval.eval_runner import run_eval; run_eval('eval/test_cases.json', 'results/eval_results.json')"

test:
	python -c "\
from engine.validator import check_format_compliance; \
r = check_format_compliance('MATCH STATE: x\nMOMENTUM: x\nKEY BATTLEGROUND: x\nOUTCOME RANGE: x\nANALYST TAKE: x', 'match_analyst'); \
assert r['compliant'] == True, 'Validator broken'; \
print('Validator OK')"
