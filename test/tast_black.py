import subprocess


def test_black():  # , "-vv"
    p = subprocess.run(["black", "-v", "--check", ".", "..\src"])
    assert p.returncode == 0
