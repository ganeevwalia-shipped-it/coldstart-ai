"""
Tests for Cold Start AI — Structured Output Schemas
Tests schema definitions, output validation, format instructions, and logging.
"""
import json
import os
import tempfile
import pytest

from app.agents.schemas import (
    AGENT_SCHEMAS,
    validate_output_structure,
    get_format_instructions,
    _log_validation_failure,
    VALIDATION_LOG_PATH,
)


class TestAgentSchemas:
    def test_priority_agents_have_schemas(self):
        priority = ["icp_architect", "positioning_strategist", "channel_mapper", "sales_playbook"]
        for agent_id in priority:
            assert agent_id in AGENT_SCHEMAS, f"Missing schema for {agent_id}"

    def test_all_schemas_have_required_sections(self):
        for agent_id, schema in AGENT_SCHEMAS.items():
            assert "required_sections" in schema, f"{agent_id} missing required_sections"
            assert len(schema["required_sections"]) >= 3, f"{agent_id} has too few sections"

    def test_all_schemas_have_format_instructions(self):
        for agent_id, schema in AGENT_SCHEMAS.items():
            assert "format_instructions" in schema, f"{agent_id} missing format_instructions"
            assert len(schema["format_instructions"]) > 50, f"{agent_id} format_instructions too short"

    def test_format_instructions_mention_mandatory(self):
        for agent_id, schema in AGENT_SCHEMAS.items():
            assert "MANDATORY" in schema["format_instructions"], \
                f"{agent_id} format_instructions should mention MANDATORY"


class TestValidateOutputStructure:
    def test_complete_icp_output(self):
        content = """
## ICP DOCUMENT — TestCo

### Primary ICP
Series A SaaS founders...

### Qualifying Criteria
1. Company has 10-50 employees
2. Using legacy tools

### Disqualifying Criteria
1. Enterprise (1000+ employees)
2. Non-tech industry

### Core Pains
1. Can't scale outbound
2. No pipeline visibility
3. Founders doing everything

### Desired Outcomes
1. Predictable pipeline
2. Repeatable sales process
3. Hire first AE confidently

### Anti-ICP
Don't sell to agencies, consulting firms, or pre-revenue startups

### Buying Signals
1. Hiring SDRs
2. Posted about growth challenges

### Lead Qualification
| Criteria | Weight | Score |
"""
        result = validate_output_structure("icp_architect", content)
        assert result["valid"] is True
        assert result["missing"] == []
        assert result["completeness"] == 1.0

    def test_missing_sections_detected(self):
        content = """
### Primary ICP
Some content here

### Anti-ICP
Some content here
"""
        result = validate_output_structure("icp_architect", content)
        assert result["valid"] is False
        assert len(result["missing"]) > 0
        assert result["completeness"] < 1.0

    def test_unknown_agent_returns_valid(self):
        result = validate_output_structure("unknown_agent", "any content")
        assert result["valid"] is True
        assert result["completeness"] == 1.0

    def test_completeness_calculation(self):
        # ICP has 8 required sections, give it 4
        content = "Primary ICP\nQualifying Criteria\nDisqualifying Criteria\nCore Pains"
        result = validate_output_structure("icp_architect", content)
        assert result["completeness"] == 0.5  # 4/8

    def test_case_insensitive_matching(self):
        content = "primary icp\nqualifying criteria\ndisqualifying criteria\ncore pains\ndesired outcomes\nanti-icp\nbuying signals\nlead qualification"
        result = validate_output_structure("icp_architect", content)
        assert result["valid"] is True

    def test_positioning_complete(self):
        content = """
Core Positioning statement here
One-Liner for the product
Value Props listed below
Proof Points with metrics
Objections buyers raise
Rebuttals to each objection
Messaging Hierarchy with pillars
Copy Bank with ready text
"""
        result = validate_output_structure("positioning_strategist", content)
        assert result["valid"] is True

    def test_channel_mapper_complete(self):
        content = """
Channel Stack ranked
Channel Kill List
90-Day Roadmap week by week
Budget Scenarios for different levels
Kill Criteria for each channel
"""
        result = validate_output_structure("channel_mapper", content)
        assert result["valid"] is True

    def test_sales_playbook_complete(self):
        content = """
Discovery Script opening
Discovery Questions list
Demo Flow structure
Objection Handling matrix
Closing Framework script
Disqualification Signals list
"""
        result = validate_output_structure("sales_playbook", content)
        assert result["valid"] is True


class TestGetFormatInstructions:
    def test_returns_instructions_for_known_agent(self):
        result = get_format_instructions("icp_architect")
        assert "MANDATORY" in result
        assert "Primary ICP" in result

    def test_returns_empty_for_unknown_agent(self):
        result = get_format_instructions("nonexistent_agent")
        assert result == ""

    def test_instructions_for_all_schema_agents(self):
        for agent_id in AGENT_SCHEMAS:
            instructions = get_format_instructions(agent_id)
            assert len(instructions) > 0, f"No instructions for {agent_id}"


class TestValidationLogging:
    def test_log_validation_failure_writes_jsonl(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            # Monkey-patch the log path
            import app.agents.schemas as schemas_module
            original_path = schemas_module.VALIDATION_LOG_PATH
            schemas_module.VALIDATION_LOG_PATH = log_path

            _log_validation_failure("test_agent", ["Section A", "Section B"], 0.75)

            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["agent_id"] == "test_agent"
            assert entry["missing_sections"] == ["Section A", "Section B"]
            assert entry["completeness"] == 0.75
            assert "timestamp" in entry

            schemas_module.VALIDATION_LOG_PATH = original_path
        finally:
            os.unlink(log_path)

    def test_validation_failure_triggers_logging(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            import app.agents.schemas as schemas_module
            original_path = schemas_module.VALIDATION_LOG_PATH
            schemas_module.VALIDATION_LOG_PATH = log_path

            # This should trigger logging because sections are missing
            validate_output_structure("icp_architect", "just some text without sections")

            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) >= 1
            entry = json.loads(lines[0])
            assert entry["agent_id"] == "icp_architect"
            assert len(entry["missing_sections"]) > 0

            schemas_module.VALIDATION_LOG_PATH = original_path
        finally:
            os.unlink(log_path)
