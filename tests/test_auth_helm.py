# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2026 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for auth-related Helm rendering."""

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CHART = REPO_ROOT / "helm" / "reana"
VALUES_DEV = REPO_ROOT / "helm" / "configurations" / "values-dev.yaml"
VALUES_CERN = REPO_ROOT / "helm" / "configurations" / "values-cern.yaml"


def _helm_template(*extra_args):
    if shutil.which("helm") is None:
        pytest.skip("helm is not installed")
    result = subprocess.run(
        ["helm", "template", "reana", str(CHART), *extra_args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_local_keycloak_auth_uses_secret_backed_reana_auth():
    rendered = _helm_template("-f", str(VALUES_DEV))

    assert "REANA_AUTH_ISSUER" in rendered
    assert "https://localhost:30443/keycloak/realms/reana" in rendered
    assert "name: reana-auth-secrets" in rendered
    assert "key: REANA_AUTH_WEB_CLIENT_SECRET" in rendered
    assert "LOGIN_PROVIDERS" not in rendered
    assert "CERN_CONSUMER" not in rendered
    assert "EOSC_CONSUMER" not in rendered


def test_cern_profile_renders_without_bundled_keycloak():
    rendered = _helm_template("-f", str(VALUES_DEV), "-f", str(VALUES_CERN))

    assert "https://auth.cern.ch/auth/realms/cern" in rendered
    assert "REANA_AUTH_ROLE_SOURCES" in rendered
    assert "resource_access.reana-server.roles" in rendered
    assert "REANA_GROUP_BACKEND_CERN_CLIENT_SECRET" not in rendered
    assert "name: reana-keycloak" not in rendered
    assert "LOGIN_PROVIDERS" not in rendered


def test_cern_profile_can_enable_cern_group_backend():
    rendered = _helm_template(
        "-f",
        str(VALUES_DEV),
        "-f",
        str(VALUES_CERN),
        "--set",
        "auth.cernGroupBackend.enabled=true",
        "--set",
        "auth.webClientId=alex-test-groups",
    )

    assert "REANA_GROUP_BACKENDS" in rendered
    assert '\\"type\\":\\"cern\\"' in rendered
    assert '\\"provider\\":\\"cern\\"' in rendered
    assert '\\"client_id\\":\\"alex-test-groups\\"' in rendered
    assert '\\"client_secret_env\\":\\"REANA_AUTH_WEB_CLIENT_SECRET\\"' in rendered
    assert "REANA_GROUP_BACKEND_CERN_CLIENT_SECRET" not in rendered
