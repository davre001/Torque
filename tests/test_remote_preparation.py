import json
from backend import remote_job


def test_failed_repository_preparation_preserves_identity_without_exporting_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key, value in {'TORQUE_REQUEST_ID':'a'*32, 'TORQUE_SOURCE_SHA':'b'*40,
                       'TORQUE_ACCEPTANCE_PROFILE':'repository-tests',
                       'TORQUE_SOURCE_REPOSITORY':'owner/repo',
                       'TORQUE_REPOSITORY_SETUP':'{}', 'TORQUE_FILES_BUNDLE':'fixture'}.items():
        monkeypatch.setenv(key, value)
    def fail(*args):
        raise ValueError('fixture-sensitive-value')
    monkeypatch.setattr('backend.repository_test_job.execute', fail)
    remote_job.main()
    record = json.loads((tmp_path/'remote-result/result.json').read_text())
    assert record['acceptance_profile'] == 'repository-tests'
    assert record['source_repository'] == 'owner/repo'
    assert record['request_id'] == 'a'*32
    assert record['result']['failure_kind'] == 'infrastructure'
    assert 'fixture-sensitive-value' not in json.dumps(record)
