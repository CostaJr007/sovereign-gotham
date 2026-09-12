"""
Sovereign Gotham - Compliance & Rules of Engagement (ROE) Engine
Strictly validates proposed actions and procedures against institutional doctrine and legal restrictions.
"""

from __future__ import annotations

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Agent_Role,
    Procedure,
    ValidateComplianceRequest,
    ValidateComplianceResponse,
)

CLEARANCE_HIERARCHY: dict[str, int] = {
    "UNCLASSIFIED": 0,
    "CONFIDENTIAL": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
    "TS_SCI": 4,
}


class ComplianceEngine:
    """
    Doctrinal compliance engine.
    Audits actions against clearance levels, command authorities, and ROE prohibitions.
    """

    def __init__(self, graph: GothamKnowledgeGraph):
        self.graph = graph

    def validate(self, request: ValidateComplianceRequest) -> ValidateComplianceResponse:
        violations: list[str] = []
        enforced: list[str] = []
        roe_status = "PERMITTED"

        # 1. Fetch Procedure and Agent Role from Knowledge Graph
        proc_obj = self.graph.get_object(request.procedure_id)
        role_obj = self.graph.get_object(request.agent_role_id)

        if not proc_obj or not isinstance(proc_obj, Procedure):
            return ValidateComplianceResponse(
                compliant=False,
                violations=[f"Procedure {request.procedure_id} not registered in sovereign ontology."],
                restrictions_enforced=[],
                roe_status="BLOCKED_UNKNOWN_PROCEDURE",
            )

        if not role_obj or not isinstance(role_obj, Agent_Role):
            return ValidateComplianceResponse(
                compliant=False,
                violations=[f"Agent Role {request.agent_role_id} not registered in sovereign ontology."],
                restrictions_enforced=[],
                roe_status="BLOCKED_UNKNOWN_ROLE",
            )

        # 2. Clearance Level Check
        role_clr_str = role_obj.clearance_level.value if hasattr(role_obj.clearance_level, "value") else str(role_obj.clearance_level)
        proc_clr_str = proc_obj.required_clearance.value if hasattr(proc_obj.required_clearance, "value") else str(proc_obj.required_clearance)

        role_rank = CLEARANCE_HIERARCHY.get(role_clr_str, 0)
        proc_rank = CLEARANCE_HIERARCHY.get(proc_clr_str, 2)
        if role_rank < proc_rank:
            violations.append(
                f"Clearance mismatch: Role {role_obj.designation} ({role_clr_str}) "
                f"lacks required clearance for {proc_obj.name} ({proc_clr_str})."
            )
            roe_status = "BLOCKED_CLEARANCE"

        # 3. Command Authority Check
        authorized_chain = self.graph.find_authorization_chain(role_obj.id, proc_obj.id)
        action_name = request.action_name.lower()
        has_direct_authority = any(
            action_name in auth.lower() or "authorize" in auth.lower() or "execute" in auth.lower()
            for auth in role_obj.decision_authority
        )

        if not authorized_chain and not has_direct_authority:
            violations.append(
                f"Authority deficiency: Role {role_obj.designation} does not possess formal decision authority "
                f"to sanction or execute action '{request.action_name}' under procedure {proc_obj.id}."
            )
            if roe_status == "PERMITTED":
                roe_status = "BLOCKED_AUTHORITY"

        # 4. ROE and Operational Restrictions Audit
        ctx = request.context or {}
        for restriction in proc_obj.restrictions:
            enforced.append(restriction)
            rest_lower = restriction.lower()

            # Rule: Diplomatic compound prohibition
            if "diplomatic" in rest_lower and ctx.get("in_diplomatic_compound", False):
                violations.append(f"ROE Breach: Operation inside sovereign diplomatic compound is strictly prohibited ({restriction}).")
                roe_status = "PROHIBITED_LEGAL"

            # Rule: Mass transit proximity during daytime
            if "transit" in rest_lower and ctx.get("near_civilian_transit", False) and ctx.get("is_daytime", False):
                violations.append(f"ROE Breach: Kinetic or exfiltration actions near civilian transit hubs during daytime prohibited ({restriction}).")
                roe_status = "BLOCKED_ROE"

            # Rule: Civilian telecom non-disruption
            if "telecom" in rest_lower and ctx.get("disrupts_civilian_infrastructure", False):
                violations.append(f"ROE Breach: Electronic disruption affecting civilian critical telecom prohibited ({restriction}).")
                roe_status = "PROHIBITED_LEGAL"

            # Rule: Lethal force ROE
            if "lethal force" in rest_lower and ctx.get("use_lethal_force", False) and not ctx.get("under_active_hostile_fire", False):
                violations.append(f"ROE Breach: Lethal countermeasures unauthorized without active incoming hostile fire ({restriction}).")
                roe_status = "PROHIBITED_LEGAL"

        is_compliant = len(violations) == 0
        return ValidateComplianceResponse(
            compliant=is_compliant,
            violations=violations,
            restrictions_enforced=enforced,
            roe_status=roe_status if not is_compliant else "PERMITTED",
        )
