import ast

from fastapi_to_skill.generators import generate_cli, generate_skill
from fastapi_to_skill.parser import parse_spec


def test_generate_cli_valid_python(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    cli_path = generate_cli(api, tmp_path)
    assert cli_path.exists()
    code = cli_path.read_text()
    ast.parse(code)
    assert "list-pets" in code
    assert "create-pet" in code
    assert "get-pet" in code
    assert "delete-pet" in code


def test_generate_cli_has_search(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    assert "search" in code
    assert "search_commands" in code


# --- Claude Code target ---


def test_generate_skill_claude_code(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    assert skill_path.exists()
    content = skill_path.read_text()
    assert "Petstore" in content
    assert "list-pets" in content
    assert content.startswith("---")
    assert "name:" in content
    assert "description:" in content
    # Claude Code specific
    assert "allowed-tools:" in content
    assert "${CLAUDE_SKILL_DIR}" in content
    # Should NOT have OpenClaw metadata
    assert "metadata:" not in content
    assert "openclaw:" not in content


def test_generate_skill_claude_code_has_setup(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    content = skill_path.read_text()
    assert "Setup" in content
    assert "pip install" in content
    assert "PETSTORE_TOKEN" in content


def test_generate_skill_claude_code_auth(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    content = skill_path.read_text()
    assert "Authentication" in content
    assert "PETSTORE_TOKEN" in content


# --- OpenClaw target ---


def test_generate_skill_openclaw(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="openclaw")
    assert skill_path.exists()
    content = skill_path.read_text()
    assert "Petstore" in content
    assert "list-pets" in content
    assert content.startswith("---")
    assert "name:" in content
    assert "description:" in content
    # OpenClaw specific
    assert "version:" in content
    assert "license: MIT-0" in content
    assert "metadata:" in content
    assert "openclaw:" in content
    assert "requires:" in content
    assert "python3" in content
    assert "primaryEnv:" in content
    # Should NOT have Claude Code specifics
    assert "allowed-tools:" not in content
    assert "${CLAUDE_SKILL_DIR}" not in content


def test_generate_skill_openclaw_env_vars(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="openclaw")
    content = skill_path.read_text()
    assert "PETSTORE_BASE_URL" in content
    assert "PETSTORE_TOKEN" in content


def test_generate_skill_openclaw_install(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="openclaw")
    content = skill_path.read_text()
    assert "install:" in content
    assert "kind: uv" in content
    assert "typer" in content
    assert "httpx" in content


# --- Default target ---


def test_generate_skill_default_is_claude_code(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path)
    content = skill_path.read_text()
    assert "allowed-tools:" in content
    assert "${CLAUDE_SKILL_DIR}" in content


# --- Full pipeline ---


def test_full_pipeline_claude_code(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    cli_path = generate_cli(api, tmp_path)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    assert cli_path.exists()
    assert skill_path.exists()
    ast.parse(cli_path.read_text())


def test_full_pipeline_openclaw(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    cli_path = generate_cli(api, tmp_path)
    skill_path = generate_skill(api, tmp_path, target="openclaw")
    assert cli_path.exists()
    assert skill_path.exists()
    ast.parse(cli_path.read_text())


# --- Complex spec tests ---


def test_complex_cli_valid_python(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    ast.parse(code)


def test_complex_cli_command_names(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    # Clean names, no path segments leaking
    assert '"list-users"' in code
    assert '"create-user"' in code
    assert '"create-order"' in code
    assert '"get-order"' in code
    assert '"get-stats"' in code
    # Should NOT have ugly suffixes
    assert '"create-order-users"' not in code
    assert '"get-stats-admin"' not in code


def test_complex_cli_body_schema_enum(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    # Enum values should appear in docstring
    assert "enum(" in code
    assert "'admin'" in code
    assert "'customer'" in code
    assert "'seller'" in code


def test_complex_cli_body_schema_nested(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    # Nested Address fields should appear
    assert "street:" in code
    assert "city:" in code
    assert "Address" in code


def test_complex_cli_query_and_body(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    code = cli_path.read_text()
    # update_user should have both --notify and --body
    assert '"--notify"' in code
    assert '"--body"' in code


def test_complex_skill_multiple_tags(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    content = skill_path.read_text()
    assert "### users" in content
    assert "### orders" in content
    assert "### admin" in content


def test_complex_full_pipeline(complex_spec, tmp_path):
    api = parse_spec(complex_spec)
    cli_path = generate_cli(api, tmp_path)
    skill_path = generate_skill(api, tmp_path, target="claude-code")
    assert cli_path.exists()
    assert skill_path.exists()
    ast.parse(cli_path.read_text())


# --- Codex target ---


def test_generate_skill_codex(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="codex")
    assert skill_path.exists()
    content = skill_path.read_text()
    assert "Petstore" in content
    assert "list-pets" in content
    # Codex format: no frontmatter, no CLAUDE_SKILL_DIR
    assert "---" not in content
    assert "${CLAUDE_SKILL_DIR}" not in content
    assert "openclaw" not in content.lower()
    # Should have standard sections
    assert "## Setup" in content
    assert "## Available Commands" in content
    assert "## Examples" in content


def test_generate_skill_codex_auth(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    skill_path = generate_skill(api, tmp_path, target="codex")
    content = skill_path.read_text()
    assert "Authentication" in content
    assert "PETSTORE_TOKEN" in content


def test_full_pipeline_codex(petstore_spec, tmp_path):
    api = parse_spec(petstore_spec)
    cli_path = generate_cli(api, tmp_path)
    skill_path = generate_skill(api, tmp_path, target="codex")
    assert cli_path.exists()
    assert skill_path.exists()
    ast.parse(cli_path.read_text())
