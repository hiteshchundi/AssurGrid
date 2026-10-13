from pathlib import Path

from app.demo.policies import build_policies, export_policies, identity


def test_fixture_profiles_and_frequencies_preserve_history():
    data = build_policies()
    assert {key:len(rows) for key, rows in data.items()} == {
        'control_definition':4, 'governance_policy':2, 'policy_version':3, 'policy_control_rule':10}
    assert data == build_policies()
    rules = {row['id']:row for row in data['policy_control_rule']}
    assert rules[identity('rule/HIGH_GXP/1/PCR')]['frequency_months'] == 24
    assert rules[identity('rule/HIGH_GXP/2/PCR')]['frequency_months'] == 12
    assert rules[identity('rule/HIGH_GXP/2/ATR')]['frequency_months'] == 3
    assert rules[identity('rule/MEDIUM_GXP/1/ACCESS_REVIEW')]['frequency_months'] == 6
    assert all(row['due_soon_days'] == 30 for row in rules.values())
    assert all('SYNTHETIC' in row['change_reason'] for row in data['policy_version'])


def test_export_is_reproducible_and_matches_snapshot(tmp_path):
    first, second = tmp_path/'first.json', tmp_path/'second.json'
    export_policies(first)
    export_policies(second)
    snapshot = Path(__file__).resolve().parents[2]/'mock-data/generated/policies.json'
    assert first.read_bytes() == second.read_bytes() == snapshot.read_bytes()
