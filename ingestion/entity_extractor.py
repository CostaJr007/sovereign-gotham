"""
Sovereign Gotham - Entity & Link Extractor
Parses raw intelligence text into canonical Gotham Objects and Links.
"""

from __future__ import annotations

import re
from typing import Any

from ontology.models import (
    Agent_Role,
    ClearanceLevel,
    Document,
    LinkType,
    OntologyLink,
    Operation,
    OperationStatus,
    Procedure,
    ProcedureCategory,
    Target_Entity,
    TargetType,
    ThreatLevel,
)


class OntologicalEntityExtractor:
    """
    Transforms unstructured/semi-structured declassified documents into
    first-class Ontological Objects and Typed Links.
    """

    @classmethod
    def extract_from_document_payload(
        cls, payload: dict[str, Any]
    ) -> tuple[list[Any], list[OntologyLink]]:
        """
        Main pipeline: returns (entities_list, links_list).
        """
        raw_text = payload.get("raw_content", "")
        entities: list[Any] = []
        links: list[OntologyLink] = []

        # 1. Create Document Object
        doc = Document(
            id=payload["id"],
            source=payload["source"],
            title=payload["title"],
            document_date=payload["document_date"],
            classification_original=payload["classification_original"],
            summary=payload["summary"],
            raw_content=raw_text,
            provenance_hash=payload.get("provenance_hash"),
        )
        entities.append(doc)

        # 2. Extract Operation
        operation = cls._extract_operation(raw_text)
        if operation:
            entities.append(operation)
            # Link: Document REGISTERS Operation
            links.append(
                OntologyLink(
                    source_id=doc.id,
                    source_type="Document",
                    target_id=operation.id,
                    target_type="Operation",
                    link_type=LinkType.REGISTERS,
                    notes=f"Document {doc.id} formally registers campaign {operation.codename}",
                )
            )

        # 3. Extract Target Entities
        targets = cls._extract_targets(raw_text)
        for target in targets:
            entities.append(target)
            if operation:
                # Link: Target ASSOCIATED_WITH Operation
                links.append(
                    OntologyLink(
                        source_id=target.id,
                        source_type="Target_Entity",
                        target_id=operation.id,
                        target_type="Operation",
                        link_type=LinkType.ASSOCIATED_WITH,
                        notes=f"Target {target.name} flagged under operation {operation.codename}",
                    )
                )

        # 4. Extract Procedures
        procedures = cls._extract_procedures(raw_text)
        for proc in procedures:
            entities.append(proc)
            if operation:
                # Link: Operation EXECUTES Procedure
                links.append(
                    OntologyLink(
                        source_id=operation.id,
                        source_type="Operation",
                        target_id=proc.id,
                        target_type="Procedure",
                        link_type=LinkType.EXECUTES,
                        notes=f"Operation {operation.codename} sanctions doctrine {proc.name}",
                    )
                )
            # Link: Procedure TARGETS relevant targets
            for target in targets:
                links.append(
                    OntologyLink(
                        source_id=proc.id,
                        source_type="Procedure",
                        target_id=target.id,
                        target_type="Target_Entity",
                        link_type=LinkType.TARGETS,
                        notes=f"Procedure {proc.name} applies to {target.name}",
                    )
                )

        # 5. Extract Agent Roles
        roles = cls._extract_agent_roles(raw_text)
        for role in roles:
            entities.append(role)
            if operation:
                # Link: Agent_Role AUTHORIZES Operation (if supervisory)
                if any("Chief" in c or "Authorize" in a for c in role.competencies for a in role.decision_authority):
                    links.append(
                        OntologyLink(
                            source_id=role.id,
                            source_type="Agent_Role",
                            target_id=operation.id,
                            target_type="Operation",
                            link_type=LinkType.AUTHORIZES,
                            notes=f"Role {role.designation} maintains command authority over {operation.codename}",
                        )
                    )

            # Link: Agent_Role AUTHORIZES or EXECUTES Procedure
            for proc in procedures:
                can_authorize = False
                for auth in role.decision_authority:
                    if "Authorize" in auth or "Sanction" in auth:
                        can_authorize = True
                        break

                if can_authorize:
                    links.append(
                        OntologyLink(
                            source_id=role.id,
                            source_type="Agent_Role",
                            target_id=proc.id,
                            target_type="Procedure",
                            link_type=LinkType.AUTHORIZES,
                            notes=f"Role {role.designation} holds formal authority to sanction {proc.name}",
                        )
                    )

        return entities, links

    @classmethod
    def _extract_operation(cls, text: str) -> Operation | None:
        """Parse operational name, codename and mandate."""
        match = re.search(r"(?:Operation Codename|Codename|PROJECT)\s*:\s*([A-Z0-9_\-]+)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"\b(OP_[A-Z0-9_\-]+)\b", text)

        if match:
            codename = match.group(1).strip().upper()
            if not codename.startswith("OP_"):
                codename = f"OP_{codename}"

            obj_match = re.search(r"Mandate\s*:\s*(.+?)(?:\n|\r)", text, re.IGNORECASE)
            objective = obj_match.group(1).strip() if obj_match else f"Classified mandate for {codename}"

            return Operation(
                id=codename,
                codename=codename,
                objective=objective,
                status=OperationStatus.ACTIVE,
                priority="HIGH",
            )
        return None

    @classmethod
    def _extract_targets(cls, text: str) -> list[Target_Entity]:
        """Extract primary and secondary targets/threat vectors."""
        targets = []
        # Pattern 1: Target Entity: NAME (Type: ..., Threat Level: ...)
        pattern = re.compile(
            r"(?:Target Entity|Target|Secondary Target)\s*:\s*([A-Za-z0-9_\-]+)(?:\s*\((?:Type:\s*([A-Za-z_]+))?(?:,\s*Threat Level:\s*([A-Za-z_]+))?\))?",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            name = match.group(1).strip()
            raw_type = match.group(2)
            raw_threat = match.group(3)

            target_type = TargetType.INDIVIDUAL
            if raw_type:
                rt_upper = raw_type.upper()
                if "ORG" in rt_upper:
                    target_type = TargetType.ORGANIZATION
                elif "INFRA" in rt_upper:
                    target_type = TargetType.INFRASTRUCTURE
                elif "THREAT" in rt_upper or "VECTOR" in rt_upper:
                    target_type = TargetType.THREAT_VECTOR

            threat_level = ThreatLevel.HIGH
            if raw_threat:
                th_upper = raw_threat.upper()
                if "CRITICAL" in th_upper:
                    threat_level = ThreatLevel.CRITICAL
                elif "MEDIUM" in th_upper:
                    threat_level = ThreatLevel.MEDIUM
                elif "LOW" in th_upper:
                    threat_level = ThreatLevel.LOW

            target_id = f"TARGET_{re.sub(r'[^A-Z0-9_]', '_', name.upper())}"
            # Deduplicate
            if not any(t.id == target_id for t in targets):
                targets.append(
                    Target_Entity(
                        id=target_id,
                        name=name,
                        type=target_type,
                        threat_level=threat_level,
                        affiliations=["Classified Surveillance Network"],
                    )
                )
        return targets

    @classmethod
    def _extract_procedures(cls, text: str) -> list[Procedure]:
        """Extract procedures, steps, and restrictions."""
        procedures = []
        # Split text into procedure blocks
        blocks = re.split(r"(?:PROCEDURE\s*ID\s*:|[A-Z]\.\s*PROCEDURE\s*:)", text, flags=re.IGNORECASE)

        for block in blocks[1:]:
            lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
            if not lines:
                continue

            first_line = lines[0]
            # Procedure ID
            id_match = re.search(r"^([A-Z0-9_\-]+)", first_line)
            proc_id = id_match.group(1).strip() if id_match else f"PROC_{len(procedures) + 1}"

            # Name
            name_match = re.search(r"Name\s*:\s*(.+)", block, re.IGNORECASE)
            proc_name = name_match.group(1).strip() if name_match else proc_id.replace("_", " ").title()

            # Category
            cat_match = re.search(r"Category\s*:\s*([A-Za-z_]+)", block, re.IGNORECASE)
            category = ProcedureCategory.HUMINT
            if cat_match:
                cm = cat_match.group(1).upper()
                for c in ProcedureCategory:
                    if c.value in cm:
                        category = c
                        break

            # Steps
            steps = []
            steps_match = re.search(r"(?:Authorized Steps|Steps)\s*:\s*(.+?)(?:Restrictions|ROE|\Z)", block, re.IGNORECASE | re.DOTALL)
            if steps_match:
                step_lines = steps_match.group(1).splitlines()
                for sl in step_lines:
                    cleaned_step = re.sub(r"^\s*[0-9]+[\.\)]\s*", "", sl).strip()
                    if cleaned_step:
                        steps.append(cleaned_step)

            # Restrictions
            restrictions = []
            rest_match = re.search(r"(?:Restrictions and ROE|Restrictions|ROE)\s*:\s*(.+?)(?:[0-9]\.|\Z)", block, re.IGNORECASE | re.DOTALL)
            if rest_match:
                rest_lines = rest_match.group(1).splitlines()
                for rl in rest_lines:
                    cleaned_r = re.sub(r"^\s*[-*•]\s*", "", rl).strip()
                    if cleaned_r:
                        restrictions.append(cleaned_r)

            # Required Clearance
            clearance = ClearanceLevel.SECRET
            if any("TOP_SECRET" in r or "TS_SCI" in r for r in restrictions):
                clearance = ClearanceLevel.TOP_SECRET

            procedures.append(
                Procedure(
                    id=proc_id,
                    name=proc_name,
                    category=category,
                    steps=steps or ["Execute authorized SOP according to standard field manual."],
                    restrictions=restrictions or ["Comply with general rules of engagement."],
                    required_clearance=clearance,
                )
            )
        return procedures

    @classmethod
    def _extract_agent_roles(cls, text: str) -> list[Agent_Role]:
        """Extract roles, designations, clearances, competencies, and decision authorities."""
        roles = []
        blocks = re.split(r"(?:Agent Role\s*:|Agent_Role\s*:)", text, flags=re.IGNORECASE)

        for block in blocks[1:]:
            lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
            if not lines:
                continue

            first_line = lines[0]
            role_id_match = re.search(r"^([A-Z0-9_\-]+)", first_line)
            role_id = role_id_match.group(1).strip() if role_id_match else f"ROLE_{len(roles) + 1}"

            # Designation
            desig_match = re.search(r"\(([^\)]+)\)", first_line)
            designation = desig_match.group(1).strip() if desig_match else role_id.replace("_", " ").title()

            # Clearance
            clear_match = re.search(r"Clearance\s*:\s*([A-Za-z_]+)", block, re.IGNORECASE)
            clearance = ClearanceLevel.SECRET
            if clear_match:
                cm = clear_match.group(1).upper()
                for c in ClearanceLevel:
                    if c.value in cm:
                        clearance = c
                        break

            # Competencies
            comp_match = re.search(r"Competencies\s*:\s*(.+?)(?:\n|\r)", block, re.IGNORECASE)
            competencies = []
            if comp_match:
                competencies = [c.strip() for c in comp_match.group(1).split(",") if c.strip()]

            # Decision Authority
            auth_match = re.search(r"Decision Authority\s*:\s*(.+?)(?:\n\n|\n[0-9]\.|\Z)", block, re.IGNORECASE | re.DOTALL)
            authorities = []
            if auth_match:
                authorities = [a.strip() for a in auth_match.group(1).replace("\n", ",").split(",") if a.strip()]

            new_role = Agent_Role(
                id=role_id,
                designation=designation,
                clearance_level=clearance,
                competencies=competencies or ["Field Operations"],
                decision_authority=authorities or ["Standard Tactical Execution"],
            )
            existing_idx = next((idx for idx, r in enumerate(roles) if r.id == new_role.id), None)
            if existing_idx is None:
                roles.append(new_role)
            else:
                existing = roles[existing_idx]
                clr_str = new_role.clearance_level.value if hasattr(new_role.clearance_level, "value") else str(new_role.clearance_level)
                if len(new_role.decision_authority) > len(existing.decision_authority) or clr_str in ["TOP_SECRET", "TS_SCI"]:
                    roles[existing_idx] = new_role
        return roles
