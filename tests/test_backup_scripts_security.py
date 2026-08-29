from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backup_script_supports_encryption_retention_and_acl_hardening():
    script = (ROOT / "scripts" / "backup_database.ps1").read_text(encoding="utf-8")

    assert "$GpgRecipient" in script
    assert "$RetentionDays" in script
    assert "$RestrictAcl" in script
    assert "--encrypt" in script
    assert "Remove-Item -Path $OutputPath -Force" in script
    assert "GpgRecipient est obligatoire en production" in script
    assert "BackupDir doit pointer vers un stockage distinct" in script


def test_windows_scripts_do_not_contain_personal_default_paths():
    scripts = [
        "backup_database.ps1",
        "restore_database.ps1",
        "run_automation.ps1",
        "install_windows_task.ps1",
    ]

    for name in scripts:
        content = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        assert "Split-Path -Parent $PSScriptRoot" in content


def test_restore_script_supports_encrypted_backups():
    script = (ROOT / "scripts" / "restore_database.ps1").read_text(encoding="utf-8")

    assert "$GpgPath" in script
    assert 'EndsWith(".gpg")' in script
    assert "--decrypt" in script
    assert "Remove-Item -Path $TempPath -Force" in script
