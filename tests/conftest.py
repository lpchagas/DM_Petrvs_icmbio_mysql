"""Fixtures compartilhadas da suíte de testes do pgd-ocde-icmbio.

Nenhum teste desta suíte abre conexão de rede ou JDBC — ver tests/README.md
para a decisão de não mockar jpype/Denodo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# lib/ e ocde/ são pacotes na raiz do projeto (mesmo padrão de bootstrap usado
# pelos scripts IND_XX.1_run.py) — necessário para "import lib.xxx"/"import ocde.xxx".
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
