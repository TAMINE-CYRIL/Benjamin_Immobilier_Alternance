from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backup_script_supports_encryption_retention_and_acl_hardening():
    script = (ROOT / "scripts" / "backup_database.ps1").read_text(encoding="utf-8")

    assert "$GpgRecipient" in script
    assert "$RetentionDays" in script
    assert "$RestrictAcl" in script
    assert "--encrypt" in script
    assert "Remove-Item -Path $OutputPath -Force" in script


def test_restore_script_supports_encrypted_backups():
    script = (ROOT / "scripts" / "restore_database.ps1").read_text(encoding="utf-8")

    assert "$GpgPath" in script
    assert 'EndsWith(".gpg")' in script
    assert "--decrypt" in script
    assert "Remove-Item -Path $TempPath -Force" in script
