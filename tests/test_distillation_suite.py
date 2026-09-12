"""
Unit tests for Sovereign Gotham Knowledge Distillation Suite.
Verifies Teacher Engine, DSpark Curator Filter, and Pipeline integrity.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from distillation.curator_filter import DistillationCuratorFilter
from distillation.pipeline import build_sample_ontology
from distillation.teacher_engine import DistillationTeacherEngine, RawDistillSample


@pytest.fixture
def sample_graph():
    return build_sample_ontology()


@pytest.fixture
def teacher_engine(sample_graph):
    return DistillationTeacherEngine(sample_graph)


@pytest.fixture
def curator_filter():
    return DistillationCuratorFilter()


def test_teacher_synthesis(teacher_engine):
    doc_rec = {
        "doc_id": "TEST-DOC-101",
        "title": "TEST INTELLIGENCE REPORT",
        "body": "Clandestine courier spotted moving across diplomatic perimeter. Urgent response mandated.",
        "classification": "SECRET // NOFORN",
    }
    sample = teacher_engine.synthesize_ontological_reasoning(doc_rec)
    assert isinstance(sample, RawDistillSample)
    assert sample.source_id == "TEST-DOC-101"
    assert "<thought>" in f"<thought>{sample.teacher_thought}</thought>"
    assert "course_of_action" in sample.teacher_output
    assert sample.teacher_output["confidence_score"] >= 0.80


def test_curator_filter_approval(curator_filter, teacher_engine):
    doc_rec = {
        "doc_id": "TEST-DOC-102",
        "title": "VERIFIED DISPATCH",
        "body": "Operational report on SIGINT interception in sector Charlie.",
        "classification": "TOP SECRET // SI-TK // NOFORN",
    }
    raw = teacher_engine.synthesize_ontological_reasoning(doc_rec)
    ok, reason = curator_filter.audit_sample(raw)
    assert ok is True
    assert reason == "PASSED"


def test_curator_filter_rejections(curator_filter):
    # Shallow reasoning rejection
    shallow_sample = RawDistillSample(
        source_id="BAD-01",
        directive="Do something",
        context={},
        teacher_thought="Too short",
        teacher_output={"document_id": "X", "threat_rating": "LOW", "course_of_action": [], "confidence_score": 0.9},
    )
    ok, reason = curator_filter.audit_sample(shallow_sample)
    assert ok is False
    assert "Reasoning trace too short" in reason

    # Low confidence rejection
    low_conf_sample = RawDistillSample(
        source_id="BAD-02",
        directive="Do something else",
        context={},
        teacher_thought="1. Step one of comprehensive intelligence analysis.\n2. Step two of threat modeling and counter-intelligence.\n3. Step three of strategic risk assessment and operational directive.",
        teacher_output={"document_id": "X", "threat_rating": "LOW", "course_of_action": ["action"], "confidence_score": 0.50},
    )
    ok, reason = curator_filter.audit_sample(low_conf_sample)
    assert ok is False
    assert "Confidence score below threshold" in reason


def test_curator_export(curator_filter, teacher_engine, tmp_path):
    doc_rec = {
        "doc_id": "TEST-DOC-103",
        "title": "EXPORT TEST RECORD",
        "body": "Detailed record regarding clandestine communications and asset extraction.",
        "classification": "SECRET",
    }
    raw = teacher_engine.synthesize_ontological_reasoning(doc_rec)
    out_file = tmp_path / "test_curated.jsonl"
    approved, rejected = curator_filter.curate_and_export([raw], output_file=out_file)
    assert approved == 1
    assert rejected == 0
    assert out_file.exists()


def test_curator_empty_list_handling(curator_filter, tmp_path):
    out_file = tmp_path / "empty_curated.jsonl"
    approved, rejected = curator_filter.curate_and_export([], output_file=out_file)
    assert approved == 0
    assert rejected == 0
    assert out_file.exists()
