import sqlite3
from cryptography.fernet import Fernet
import pytest
from backend import database_backup as backup


def test_encrypted_sqlite_backup_restores_committed_wal(tmp_path,monkeypatch):
    path=tmp_path/'source.db'
    source=sqlite3.connect(path)
    source.execute('PRAGMA journal_mode=WAL')
    source.execute('CREATE TABLE fixture(value TEXT)')
    source.execute('INSERT INTO fixture VALUES(?)',('private-fixture-content',));source.commit()
    monkeypatch.setenv('TORQUE_DATABASE',str(path))
    monkeypatch.setenv('TORQUE_SESSION_ENCRYPTION_KEY',Fernet.generate_key().decode())
    monkeypatch.setattr(backup,'ROOT',tmp_path)
    report=backup.backup_sqlite()
    encrypted=(tmp_path/report['encrypted_backup']).read_bytes()
    assert b'private-fixture-content' not in encrypted
    raw=backup.cipher().decrypt(encrypted)
    restored=sqlite3.connect(':memory:');restored.deserialize(raw)
    assert restored.execute('SELECT value FROM fixture').fetchone()[0]=='private-fixture-content'
    assert report['integrity_check']=='ok'
    assert source.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
    source.close();restored.close()


def test_backup_size_limit_precedes_encryption_write(tmp_path,monkeypatch):
    monkeypatch.setattr(backup,'ROOT',tmp_path)
    monkeypatch.setattr(backup,'MAX_BYTES',4)
    with pytest.raises(ValueError,match='bound'):backup.save(b'12345','fixture')
    assert not (tmp_path/'var').exists()
