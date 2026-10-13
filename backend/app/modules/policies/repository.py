"""Scoped read queries; no policy publication or obligation calculation."""
import sqlalchemy as sa

from app.db.schema import control_definition as control, governance_policy as policy, organization
from app.db.schema import policy_control_rule as rule, policy_version as version, regulated_application as application
from app.modules.applications.repository import access_condition


def list_policies(session, principal, filters):
    rows = session.execute(sa.select(policy.c.id, policy.c.policy_key, policy.c.name).where(
        policy.c.organization_id == principal.organization_id,
    ).order_by(policy.c.policy_key, policy.c.id).offset((filters.page-1)*filters.page_size)
      .limit(filters.page_size+1)).mappings().all()
    return dict(items=rows[:filters.page_size], page=filters.page, page_size=filters.page_size,
                has_more=len(rows)>filters.page_size)


def rule_columns():
    return [rule.c.id.label("rule_id"), rule.c.control_definition_id, control.c.control_key,
            control.c.name.label("control_name"), control.c.active.label("control_active"),
            rule.c.frequency_months, rule.c.due_soon_days, rule.c.mandatory, rule.c.evidence_requirement]


def rule_record(row):
    return dict(id=row["rule_id"], **{key:row[key] for key in (
        "control_definition_id", "control_key", "control_name", "control_active", "frequency_months",
        "due_soon_days", "mandatory", "evidence_requirement")})


def history(session, principal, policy_id):
    rows = session.execute(sa.select(
        policy.c.id, policy.c.policy_key, policy.c.name,
        version.c.id.label("version_id"), version.c.version_number, version.c.effective_from, version.c.effective_to,
        version.c.gxp_classification, version.c.criticality, version.c.change_reason, *rule_columns(),
    ).select_from(policy.outerjoin(version, sa.and_(version.c.policy_id == policy.c.id,
        version.c.organization_id == policy.c.organization_id)).outerjoin(rule, sa.and_(
        rule.c.policy_version_id == version.c.id, rule.c.organization_id == version.c.organization_id,
    )).outerjoin(control, sa.and_(control.c.id == rule.c.control_definition_id,
        control.c.organization_id == rule.c.organization_id))).where(
        policy.c.organization_id == principal.organization_id, policy.c.id == policy_id,
    ).order_by(version.c.version_number, control.c.control_key)).mappings().all()
    if not rows: return None
    versions = {}
    for row in rows:
        vid = row["version_id"]
        if vid is None: continue
        if vid not in versions:
            versions[vid] = dict(id=vid, **{key:row[key] for key in (
                "version_number", "effective_from", "effective_to", "gxp_classification", "criticality", "change_reason")}, rules=[])
        if row["rule_id"] is not None: versions[vid]["rules"].append(rule_record(row))
    return dict(id=rows[0]["id"], policy_key=rows[0]["policy_key"], name=rows[0]["name"], versions=list(versions.values()))


def resolve(session, principal, application_id, as_of):
    # One statement authorizes the application and reads applicable versions/rules
    # from the same snapshot. Never infer Current from missing policy data.
    rows = session.execute(sa.select(
        application.c.id.label("application_id"), organization.c.timezone,
        version.c.id.label("version_id"), version.c.version_number, version.c.effective_from, version.c.effective_to,
        policy.c.id.label("policy_id"), policy.c.policy_key, policy.c.name.label("policy_name"), *rule_columns(),
    ).select_from(application.join(organization, organization.c.id == application.c.organization_id)
      .outerjoin(version, sa.and_(version.c.organization_id == application.c.organization_id,
        version.c.gxp_classification == application.c.gxp_classification, version.c.criticality == application.c.criticality,
        version.c.effective_from <= as_of, sa.or_(version.c.effective_to.is_(None), version.c.effective_to > as_of)))
      .outerjoin(policy, sa.and_(policy.c.id == version.c.policy_id, policy.c.organization_id == application.c.organization_id))
      .outerjoin(rule, sa.and_(rule.c.policy_version_id == version.c.id, rule.c.organization_id == application.c.organization_id))
      .outerjoin(control, sa.and_(control.c.id == rule.c.control_definition_id, control.c.organization_id == application.c.organization_id)))
      .where(application.c.id == application_id, application.c.organization_id == principal.organization_id,
             access_condition(principal)).order_by(policy.c.policy_key, version.c.version_number, control.c.control_key)
    ).mappings().all()
    if not rows: return None
    candidates, rules = {}, []
    for row in rows:
        if row["version_id"] is not None:
            candidates[row["version_id"]] = dict(policy_version_id=row["version_id"], **{key:row[key] for key in (
                "policy_id", "policy_key", "policy_name", "version_number", "effective_from", "effective_to")})
        if row["rule_id"] is not None: rules.append(rule_record(row))
    if len(candidates)>1:
        configuration, explanation = "Conflicting Configuration", "Multiple policy versions match this application and date."
    elif not candidates:
        configuration, explanation = "Missing Configuration", "No policy version matches this application and date."
    elif not rules or any(not item["control_active"] for item in rules):
        configuration, explanation = "Missing Configuration", "The matching version has no rules or references inactive controls."
    else:
        configuration, explanation = "Resolved", "One policy version matches. Rules are organization defaults; overrides and obligations are not implemented."
    return dict(application_id=application_id, as_of=as_of, timezone=rows[0]["timezone"], configuration=configuration,
                explanation=explanation, candidates=list(candidates.values()), rules=rules if configuration == "Resolved" else [])
