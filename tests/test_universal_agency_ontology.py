"""
Unit & Integration Tests for Sovereign Gotham Universal Cross-Agency Ontology & Reasoning.
Verifies NSA, FBI, CIA, and DoD ontological models, coherence graph chains, and vector store retrieval.
"""

from __future__ import annotations

import pytest

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    AgencyDoctrineType,
    CIAHypothesisMatrix,
    DoDOperationalDoctrine,
    FBIActorProfile,
    LinkType,
    MissionContext,
    NSASignalVector,
    OntologyLink,
    ProblemDomain,
    UniversalMissionSolution,
)
from storage.vector_store import SovereignVectorStore


def test_problem_domain_and_doctrine_enums():
    """Validates problem domains and agency doctrine types."""
    assert ProblemDomain.CORPORATE_STRATEGY == "CORPORATE_STRATEGY"
    assert ProblemDomain.SKILL_ACQUISITION == "SKILL_ACQUISITION"
    assert ProblemDomain.SECURITY_CRISIS == "SECURITY_CRISIS"
    assert ProblemDomain.CYBER_TECH_SYSTEMS == "CYBER_TECH_SYSTEMS"

    assert AgencyDoctrineType.NSA_SIGINT_TELEMETRY == "NSA_SIGINT_TELEMETRY"
    assert AgencyDoctrineType.FBI_FORENSIC_INCENTIVE == "FBI_FORENSIC_INCENTIVE"
    assert AgencyDoctrineType.CIA_STRATEGIC_ACH == "CIA_STRATEGIC_ACH"
    assert AgencyDoctrineType.DOD_ARMY_OODA_MISSION_COMMAND == "DOD_ARMY_OODA_MISSION_COMMAND"


def test_cross_agency_entities_creation():
    """Validates instantiation of all 4 agency entities."""
    mission = MissionContext(
        id="MISSION-TEST-01",
        problem_statement="Investigate 42% drop in SaaS cash flow",
        domain=ProblemDomain.CORPORATE_STRATEGY,
        time_horizon="T+30_DAYS",
        resource_envelope=["Financial records", "Executive interviews"],
        critical_constraints=["Strict legal compliance"],
    )
    assert mission.id == "MISSION-TEST-01"
    assert mission.domain == ProblemDomain.CORPORATE_STRATEGY

    nsa_signal = NSASignalVector(
        id="SIG-01",
        metric_name="Free Cash Flow Drop",
        observed_value="-42%",
        frequency="MONTHLY",
        signal_to_noise_ratio=0.95,
        anomaly_flag=True,
        telemetry_source="ERP_DB",
    )
    assert nsa_signal.anomaly_flag is True

    fbi_actor = FBIActorProfile(
        id="ACTOR-01",
        actor_name="CCO Executive",
        stated_position="Market contraction",
        hidden_incentives=["Commission bonus on new logos"],
        vulnerabilities=["Personal debt"],
        leverage_points=["Board audit clause"],
        conflict_of_interest=True,
    )
    assert fbi_actor.conflict_of_interest is True

    cia_ach = CIAHypothesisMatrix(
        id="ACH-01",
        competing_hypotheses=["H1: Market", "H2: Software bug", "H3: Incentive misalignment"],
        diagnostic_evidence=["Enterprise churn surge while volume increased"],
        deception_risk=0.25,
        selected_hypothesis="H3: Incentive misalignment",
        analytic_confidence=0.94,
    )
    assert cia_ach.analytic_confidence == 0.94

    dod_doctrine = DoDOperationalDoctrine(
        id="DOD-01",
        orientation_ooda="Commission structure incentivizes adverse selection",
        phased_actions=[
            {"phase": "T+24h", "action": "Freeze unverified commission payouts"},
            {"phase": "T+7d", "action": "Restructure compensation with 90-day retention vesting"},
        ],
        rules_of_engagement=["No summary termination without legal audit"],
        abort_criteria=["If churn exceeds 25%, halt active customer acquisition"],
        stop_loss_trigger="25% churn threshold",
    )
    assert len(dod_doctrine.phased_actions) == 2


def test_cross_agency_coherence_chain_in_graph():
    """Validates building and traversing a multi-agency problem solving chain in GothamKnowledgeGraph."""
    graph = GothamKnowledgeGraph()

    mission = MissionContext(
        id="MISSION-TEST-02",
        problem_statement="Radar signal anomaly at northern coastal sector",
        domain=ProblemDomain.SECURITY_CRISIS,
    )
    nsa = NSASignalVector(
        id="SIG-RADAR-01",
        metric_name="9.4GHz Intermittent Pulse",
        observed_value="37-second interval",
        telemetry_source="Coastal Radar Station",
        anomaly_flag=True,
    )
    fbi = FBIActorProfile(
        id="ACTOR-RESEARCH-VESSEL",
        actor_name="Foreign Oceanographic Vessel",
        stated_position="Bathymetric survey",
        conflict_of_interest=True,
    )
    cia = CIAHypothesisMatrix(
        id="ACH-RADAR-01",
        competing_hypotheses=["H1: Atmospheric", "H2: Hardware glitch", "H3: SAR radar scan"],
        selected_hypothesis="H3: SAR radar scan",
    )
    dod = DoDOperationalDoctrine(
        id="DOD-RADAR-01",
        orientation_ooda="Platform emitting SAR pulses without civilian AIS transponder",
        rules_of_engagement=["Maintain passive reception only"],
        stop_loss_trigger="Civilian air traffic frequency interference",
    )

    graph.add_object(mission)
    graph.add_object(nsa)
    graph.add_object(fbi)
    graph.add_object(cia)
    graph.add_object(dod)

    # Add coherence links
    graph.add_link(OntologyLink(
        source_id=mission.id,
        source_type="MissionContext",
        target_id=nsa.id,
        target_type="NSASignalVector",
        link_type=LinkType.DETECTS_SIGNAL,
    ))
    graph.add_link(OntologyLink(
        source_id=mission.id,
        source_type="MissionContext",
        target_id=fbi.id,
        target_type="FBIActorProfile",
        link_type=LinkType.INVESTIGATES_INCENTIVE,
    ))
    graph.add_link(OntologyLink(
        source_id=mission.id,
        source_type="MissionContext",
        target_id=cia.id,
        target_type="CIAHypothesisMatrix",
        link_type=LinkType.EVALUATES_HYPOTHESIS,
    ))
    graph.add_link(OntologyLink(
        source_id=mission.id,
        source_type="MissionContext",
        target_id=dod.id,
        target_type="DoDOperationalDoctrine",
        link_type=LinkType.COMMANDS_ACTION,
    ))

    chain = graph.find_cross_agency_coherence_chain(mission.id)
    assert chain["mission_id"] == mission.id
    assert len(chain["nsa_signals"]) == 1
    assert len(chain["fbi_actors"]) == 1
    assert len(chain["cia_hypotheses"]) == 1
    assert len(chain["dod_actions"]) == 1
    assert len(chain["coherence_links"]) == 4


def test_universal_mission_solution_schema():
    """Validates UniversalMissionSolution Pydantic model serialization and fields."""
    solution = UniversalMissionSolution(
        mission_id="MISSION-999",
        domain=ProblemDomain.SKILL_ACQUISITION,
        problem_summary="Rapid language acquisition in 6 months",
        nsa_signal_triage={
            "metrics": "Top 1000 Zipf frequency lemmas",
            "noise_filtered": True,
        },
        fbi_behavioral_forensics={
            "actor": "Executive learner",
            "friction": "Social anxiety in oral meetings",
        },
        cia_strategic_hypotheses={
            "selected": "H3: High-frequency Zipf immersion with stress simulation",
            "deception_risk": 0.05,
        },
        dod_tactical_action_plan={
            "phases": ["T+24h: Anki audio", "T+7d: 5x weekly native tutoring", "T+30d: Handelsblatt immersion"],
            "roe": ["Zero translation to native language during speaking sessions"],
            "abort_criteria": ["If speaking fluency < 4min at day 60, restructure coaching"],
        },
        confidence_score=0.96,
    )

    data = solution.model_dump()
    assert data["mission_id"] == "MISSION-999"
    assert data["domain"] == "SKILL_ACQUISITION"
    assert data["confidence_score"] == 0.96
    assert data["sovereignty_proof"]["airgap_verified"] is True


def test_doctrinal_rag_retrieval():
    """Verifies that SovereignVectorStore indexes and retrieves agency tradecraft doctrine."""
    vs = SovereignVectorStore(persist_directory="storage/chroma_db")
    results = vs.similarity_search("Boyd OODA loop fast decision tempo and course of action", top_k=3)
    assert len(results) > 0
    # At least one result should reference DoD or OODA
    found_ooda = any("OODA" in r.get("text", "") or "DOD" in str(r.get("metadata", {})) for r in results)
    assert found_ooda is True
