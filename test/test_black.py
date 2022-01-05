import subprocess


def test_black():  # , "-vv"
    p = subprocess.run(["black", "--check", ".", "..\src"])
    assert p.returncode == 0


def t():
    pass
