"""Tilsyn onboarding enforces the existing D-003 gate/e2e contract.
Source: Aftergraph/tilsyn#7 issuecomment-6328720868; no override/owner invention.
"""
import importlib.util
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('agent_review', ROOT/'scripts/agent_review.py')
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

class TilsynPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT/'policies/pinned-checks.json').read_text())
        self.green = [{'name': n, 'status': 'COMPLETED', 'conclusion': 'SUCCESS'} for n in ('gate','e2e')]
    def test_exact_existing_contract(self):
        self.assertEqual(self.policy['checks'].get('tilsyn'), ['gate','e2e'])
    def test_both_green_pass(self):
        self.assertEqual(agent.check_pinned_checks('tilsyn', self.green, self.policy), [])
    def test_each_required_check_missing_blocks(self):
        for omitted in ('gate','e2e'):
            self.assertIn('PINNED_CHECK_MISSING', agent.check_pinned_checks('tilsyn',[c for c in self.green if c['name']!=omitted],self.policy))
    def test_each_non_success_state_blocks(self):
        for name in ('gate','e2e'):
            for status,conclusion,reason in [('IN_PROGRESS',None,'PINNED_CHECK_PENDING'),('COMPLETED','FAILURE','PINNED_CHECK_FAILED'),('COMPLETED','SKIPPED','PINNED_CHECK_FAILED'),('COMPLETED','CANCELLED','PINNED_CHECK_FAILED')]:
                checks=[dict(c, status=status, conclusion=conclusion) if c['name']==name else c.copy() for c in self.green]
                self.assertIn(reason, agent.check_pinned_checks('tilsyn',checks,self.policy))
    def test_unknown_repo_still_blocks_even_override(self):
        self.assertEqual(agent.check_pinned_checks('unregistered',self.green,self.policy,['OWNER_OVERRIDE_ACCEPT_RISK']),['POLICY_UNKNOWN_REPO'])
    def test_no_checks_blocks_even_override(self):
        self.assertIn('PINNED_CHECK_MISSING',agent.check_pinned_checks('tilsyn',[],self.policy,['OWNER_OVERRIDE_ACCEPT_RISK']))
    def test_missing_ownership_still_blocks(self):
        self.assertIn('CODEOWNERS_UNMATCHED',agent.check_binding({'codeowners_matched':False,'codeowners_independent_possible':True,'reviews':[]}))
    def test_documented_sole_owner_topology_without_fabricated_approval(self):
        self.assertEqual(agent.check_binding({'codeowners_matched':False,'codeowners_independent_possible':False,'reviews':[]}),[])
if __name__=='__main__': unittest.main()
