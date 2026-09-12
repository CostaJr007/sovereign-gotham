"""
Sovereign Gotham - Core Ontology Models (Pydantic v2)
Implements ObjectTypes, LinkTypes, and ActionTypes (Palantir O-L-A Pattern).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =====================================================================
# ENUMS & TAXONOMIES
# =====================================================================

class SecurityClassification(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    DECLASSIFIED = "DECLASSIFIED"


class ProcedureCategory(str, Enum):
    HUMINT = "HUMINT"
    COUNTER_INTELLIGENCE = "COUNTER_INTELLIGENCE"
    CYBER = "CYBER"
    EXTRACTION = "EXTRACTION"
    SURVEILLANCE = "SURVEILLANCE"
    COVERT_ACTION = "COVERT_ACTION"
    PSYOPS = "PSYOPS"


class OperationStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DECOMMISSIONED = "DECOMMISSIONED"
    COMPROMISED = "COMPROMISED"


class TargetType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    ORGANIZATION = "ORGANIZATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    THREAT_VECTOR = "THREAT_VECTOR"


class ThreatLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ClearanceLevel(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    TS_SCI = "TS_SCI"


class LinkType(str, Enum):
    REGISTERS = "REGISTERS"                   # (Document) -> (Operation)
    EXECUTES = "EXECUTES"                     # (Operation) -> (Procedure)
    AUTHORIZES = "AUTHORIZES"                 # (Agent_Role) -> (Procedure / Operation)
    TARGETS = "TARGETS"                       # (Procedure) -> (Target_Entity)
    ASSOCIATED_WITH = "ASSOCIATED_WITH"       # (Target_Entity) -> (Operation)
    MONITORS = "MONITORS"                     # (Operation) -> (Target_Entity)
    CONFLICTS_WITH = "CONFLICTS_WITH"         # (Procedure) -> (Procedure / Restriction)
    DETECTS_SIGNAL = "DETECTS_SIGNAL"         # (NSA Signal) -> (Target / Anomaly)
    CORRELATES_WITH = "CORRELATES_WITH"       # (Entity) <-> (Entity / Metric)
    INVESTIGATES_INCENTIVE = "INVESTIGATES_INCENTIVE" # (FBI Forensics) -> (Actor / Node)
    EVALUATES_HYPOTHESIS = "EVALUATES_HYPOTHESIS"     # (CIA ACH) -> (Scenario / Hypothesis)
    COMMANDS_ACTION = "COMMANDS_ACTION"       # (DoD Command) -> (CourseOfAction)
    CONSTRAINS = "CONSTRAINS"                 # (ROE Guardrail) -> (Action)


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    IMMEDIATE = "IMMEDIATE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class ProblemDomain(str, Enum):
    CORPORATE_STRATEGY = "CORPORATE_STRATEGY"
    SKILL_ACQUISITION = "SKILL_ACQUISITION"
    OPERATIONS_LOGISTICS = "OPERATIONS_LOGISTICS"
    NEGOTIATION_DISPUTE = "NEGOTIATION_DISPUTE"
    SECURITY_CRISIS = "SECURITY_CRISIS"
    CYBER_TECH_SYSTEMS = "CYBER_TECH_SYSTEMS"
    GEOPOLITICAL_RISK = "GEOPOLITICAL_RISK"


class AgencyDoctrineType(str, Enum):
    NSA_SIGINT_TELEMETRY = "NSA_SIGINT_TELEMETRY"
    FBI_FORENSIC_INCENTIVE = "FBI_FORENSIC_INCENTIVE"
    CIA_STRATEGIC_ACH = "CIA_STRATEGIC_ACH"
    DOD_ARMY_OODA_MISSION_COMMAND = "DOD_ARMY_OODA_MISSION_COMMAND"



# =====================================================================
# OBJECT TYPES (ENTITIES)
# =====================================================================

class BaseOntologyObject(BaseModel):
    """Base class for all first-class Gotham Entities."""
    id: str = Field(..., description="Unique alphanumeric identifier (e.g. DOC-1984-01, PROC-EXT-04)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore", use_enum_values=True)


class Document(BaseOntologyObject):
    """Declassified or operational source document (CIA CREST, FBI, DoD)."""
    source: str = Field(..., description="Originating agency: CIA, FBI, DoD, DIA, etc.")
    title: str = Field(..., description="Document title or subject line")
    document_date: str | None = Field(None, description="Original record date (YYYY-MM-DD)")
    classification_original: SecurityClassification = Field(default=SecurityClassification.DECLASSIFIED)
    summary: str = Field(..., description="Analytic abstract or executive summary")
    raw_content: str | None = Field(None, description="Full extracted or OCR text")
    provenance_hash: str | None = Field(None, description="SHA256 hash of original file for air-gapped custody")


class Procedure(BaseOntologyObject):
    """Doctrinal SOP, tactic, or operational playbook."""
    name: str = Field(..., description="Formal doctrine name (e.g. Hostile Area Asset Extraction)")
    category: ProcedureCategory = Field(..., description="Operational domain")
    steps: list[str] = Field(default_factory=list, description="Ordered procedural steps")
    restrictions: list[str] = Field(default_factory=list, description="Legal, diplomatic, or ROE prohibitions")
    required_clearance: ClearanceLevel = Field(default=ClearanceLevel.SECRET)
    roe_guidelines: str | None = Field(None, description="Rules of Engagement constraints")


class Operation(BaseOntologyObject):
    """Specific operational campaign or mission."""
    codename: str = Field(..., description="Operation Codename (e.g. OP_CHOPIN, OP_AEGIS)")
    start_date: str | None = Field(None, description="Initiation date")
    end_date: str | None = Field(None, description="Termination or review date")
    objective: str = Field(..., description="Primary mission mandate")
    status: OperationStatus = Field(default=OperationStatus.PLANNED)
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Operational priority")


class Agent_Role(BaseOntologyObject):
    """Operational persona, station chief, or tactical role."""
    designation: str = Field(..., description="Title/Rank/Role (e.g. Case Officer, Chief of Station, Tactical Lead)")
    clearance_level: ClearanceLevel = Field(default=ClearanceLevel.SECRET)
    competencies: list[str] = Field(default_factory=list, description="Certified skill vectors")
    decision_authority: list[str] = Field(default_factory=list, description="Actions or procedures this role is empowered to sanction")


class Target_Entity(BaseOntologyObject):
    """Subject of interest, hostile vector, or high-value target."""
    name: str = Field(..., description="Alias, handle, or identity")
    type: TargetType = Field(..., description="Individual, Organization, Infrastructure, Threat Vector")
    threat_level: ThreatLevel = Field(default=ThreatLevel.MEDIUM)
    affiliations: list[str] = Field(default_factory=list, description="Associated groups or sponsors")
    location: str | None = Field(None, description="Known operating sector or coordinate")


class MissionContext(BaseOntologyObject):
    """Target problem or mission mandate mapped into the intelligence ontology."""
    problem_statement: str = Field(..., description="Core challenge or strategic problem to resolve")
    domain: ProblemDomain = Field(..., description="Problem taxonomy domain")
    time_horizon: str = Field(default="T+30_DAYS", description="Operational time window (e.g. T+24_HOURS, T+7_DAYS, T+30_DAYS, T+6_MONTHS)")
    resource_envelope: list[str] = Field(default_factory=list, description="Available assets, tools, personnel, or budget")
    critical_constraints: list[str] = Field(default_factory=list, description="Inviolable boundaries, legal prohibitions, or stop-loss limits")


class NSASignalVector(BaseOntologyObject):
    """Objective signals intelligence, cold telemetry, and pattern detection."""
    metric_name: str = Field(..., description="Name of telemetry stream, frequency, or metric")
    observed_value: str = Field(..., description="Quantified value or factual measurement")
    frequency: str = Field(default="PERSISTENT", description="Temporal frequency (e.g. HOURLY, BURST, ANOMALOUS, PERIODIC)")
    signal_to_noise_ratio: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in signal validity vs environmental noise")
    anomaly_flag: bool = Field(default=False, description="True if telemetry deviates from historical baseline")
    telemetry_source: str = Field(..., description="Origin sensor, data feed, or cyber telemetry node")


class FBIActorProfile(BaseOntologyObject):
    """Forensic behavioral analysis, incentive structures, and network vulnerabilities."""
    actor_name: str = Field(..., description="Individual, partner, competitor, or organizational stakeholder")
    stated_position: str = Field(..., description="Public or official stated position/claim")
    hidden_incentives: list[str] = Field(default_factory=list, description="Underlying financial, reputational, or power payoffs")
    vulnerabilities: list[str] = Field(default_factory=list, description="Pressure points, dependencies, or structural weaknesses")
    leverage_points: list[str] = Field(default_factory=list, description="Actionable points of influence or negotiated settlement")
    conflict_of_interest: bool = Field(default=False, description="Whether stakeholder incentives diverge from systemic mission integrity")


class CIAHypothesisMatrix(BaseOntologyObject):
    """Richards Heuer's Analysis of Competing Hypotheses (ACH) for bias elimination."""
    competing_hypotheses: list[str] = Field(..., description="List of mutually exclusive explanatory hypotheses (H1, H2, H3)")
    diagnostic_evidence: list[str] = Field(default_factory=list, description="Facts that discriminate between hypotheses (high diagnostic value)")
    deception_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability of intentional deception, bluff, or disinformation")
    selected_hypothesis: str = Field(..., description="Most robust, least disproven hypothesis")
    analytic_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Analytic confidence level")


class DoDOperationalDoctrine(BaseOntologyObject):
    """DoD / Army Joint Planning Process, OODA Loop, and Mission Command."""
    orientation_ooda: str = Field(..., description="Orientation phase: synthesis of signals, biases, and reality gap")
    phased_actions: list[dict[str, str]] = Field(default_factory=list, description="Sequential phases: Recon, Maneuver, Exploitation, Consolidation")
    rules_of_engagement: list[str] = Field(default_factory=list, description="Inviolable operating boundaries and red lines")
    abort_criteria: list[str] = Field(default_factory=list, description="Deterministic triggers for mission abort or course reversal")
    stop_loss_trigger: str = Field(..., description="Maximum acceptable drawdown, risk threshold, or failure indicator")



# =====================================================================
# LINK TYPES (RELATIONSHIPS)
# =====================================================================

class OntologyLink(BaseModel):
    """Typed semantic edge between two Gotham Entities."""
    source_id: str = Field(..., description="ID of source entity")
    source_type: str = Field(..., description="Entity class of source (e.g. Document, Operation)")
    target_id: str = Field(..., description="ID of target entity")
    target_type: str = Field(..., description="Entity class of target")
    link_type: LinkType = Field(..., description="Directed relationship predicate")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of intelligence link")
    notes: str | None = Field(None, description="Contextual intelligence annotation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(use_enum_values=True)


# =====================================================================
# ACTION TYPES (SYSTEM ACTIONS & DECISION INTERFACES)
# =====================================================================

class EvaluateRiskRequest(BaseModel):
    scenario: str = Field(..., description="Description of the tactical situation")
    target_id: str | None = Field(None, description="Target entity ID being engaged")
    procedure_id: str | None = Field(None, description="Procedure considered")
    context: dict[str, Any] = Field(default_factory=dict, description="Environmental and temporal factors")


class EvaluateRiskResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Quantified risk metric (0-100)")
    risk_factors: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    acceptable: bool = Field(..., description="Whether risk remains within authorized operational envelope")


class ValidateComplianceRequest(BaseModel):
    action_name: str = Field(..., description="Action being audited (e.g. AuthorizeSurveillance, DirectExtraction)")
    procedure_id: str = Field(..., description="Procedure ID in question")
    agent_role_id: str = Field(..., description="Role attempting to authorize/execute")
    context: dict[str, Any] = Field(default_factory=dict)


class ValidateComplianceResponse(BaseModel):
    compliant: bool = Field(..., description="True if within all legal, ROE, and doctrine mandates")
    violations: list[str] = Field(default_factory=list, description="Specific rules or restrictions breached")
    restrictions_enforced: list[str] = Field(default_factory=list, description="Applied operational doctrine")
    roe_status: str = Field(default="PERMITTED", description="PERMITTED, BLOCKED_CLEARANCE, BLOCKED_ROE, PROHIBITED_LEGAL")


class CourseOfAction(BaseModel):
    step_number: int
    directive: str
    precaution: str


class RecommendActionRequest(BaseModel):
    scenario: str = Field(..., description="Current tactical intelligence report")
    target_id: str = Field(..., description="Target entity under review")
    agent_role_id: str = Field(..., description="Operating authority requestor")
    mandatory_constraints: list[str] = Field(default_factory=list, description="User or mission specific guardrails")


class RecommendActionResponse(BaseModel):
    recommended_procedure_id: str
    procedure_name: str
    course_of_action: list[CourseOfAction]
    rationale: str
    evidence_chain: list[OntologyLink] = Field(default_factory=list, description="Graph links justifying this decision")
    risk_assessment: EvaluateRiskResponse
    compliance_validation: ValidateComplianceResponse
    sovereignty_proof: dict[str, Any] = Field(default_factory=dict, description="Air-gap and model hash verification")


class UniversalMissionSolution(BaseModel):
    """
    Unified Cross-Agency Solution Blueprint.
    Integrates the cognitive tradecraft of NSA + FBI + CIA + DoD/Army
    to deterministically solve complex real-world and operational dilemmas.
    """
    mission_id: str = Field(..., description="Unique mission resolution ID")
    domain: ProblemDomain = Field(..., description="Problem taxonomy domain")
    problem_summary: str = Field(..., description="Concise statement of the operational challenge")
    nsa_signal_triage: dict[str, Any] = Field(
        ...,
        description="Cold signals, telemetry metrics, anomalies detected, and noise filtering",
    )
    fbi_behavioral_forensics: dict[str, Any] = Field(
        ...,
        description="Stakeholders mapped, hidden incentives identified, conflict of interest, and leverage points",
    )
    cia_strategic_hypotheses: dict[str, Any] = Field(
        ...,
        description="Richards Heuer ACH matrix: H1, H2, H3, diagnostic evidence, deception probability, and selected path",
    )
    dod_tactical_action_plan: dict[str, Any] = Field(
        ...,
        description="DoD Joint Planning / OODA: Phase 1 (T+24h), Phase 2 (T+7d), Phase 3 (T+30d), ROE constraints, and abort criteria",
    )
    confidence_score: float = Field(default=0.92, ge=0.0, le=1.0, description="Overall cross-agency confidence rating")
    sovereignty_proof: dict[str, Any] = Field(
        default_factory=lambda: {"airgap_verified": True, "curation_engine": "DSpark_Universal_v2"},
        description="Sovereignty cryptographic verification",
    )

    model_config = ConfigDict(use_enum_values=True)

