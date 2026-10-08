# AssurGrid — AG-01 Product Design

**Status:** Locked for V1  
**Purpose:** Source of truth for AssurGrid product design before AG-02 System Design & Architecture.

---

## 1. Product Purpose

AssurGrid is a governance workspace for regulated computerized systems.

Its purpose is to give Quality, Governance, Application Owners, and other authorized stakeholders a single place to understand:

- what regulated applications exist,
- who owns them,
- what lifecycle and validation state they are in,
- which governance activities apply,
- what is due soon or overdue,
- what changes, audits, findings, and CAPAs are open,
- what validation and lifecycle documents exist,
- and whether the system remains under appropriate governance.

AssurGrid should reduce fragmented tracking across spreadsheets, repositories, email, and disconnected enterprise tools.

---

## 2. Core Product Principle

AssurGrid must not hardcode one pharmaceutical company's governance process.

Instead:

> **AssurGrid provides the governance framework; authorized users configure the organization's specific rules.**

Different organizations may use different frequencies, document names, classifications, review requirements, and governance policies.

AssurGrid should therefore be configurable while maintaining strict permissions, auditability, and historical traceability.

---

## 3. Primary V1 Users

### 3.1 Quality / Governance Owner
Responsible for defining and overseeing governance requirements.

Typical responsibilities:
- configure governance rules,
- review application health,
- monitor overdue activities,
- review findings/CAPAs,
- oversee validation and periodic-review status,
- review governance exceptions.

### 3.2 Application Owner
Responsible for a specific computerized system.

Typical responsibilities:
- maintain application information,
- complete assigned governance activities,
- provide evidence,
- maintain ownership and system metadata,
- review upcoming obligations.

### 3.3 AssurGrid Administrator
Responsible for platform-level administration.

Typical responsibilities:
- manage users and roles,
- configure organization-level settings,
- manage controlled reference data,
- maintain platform configuration.

### 3.4 Read-Only / Stakeholder User
May view authorized application and governance information but cannot alter governance rules.

Exact role names and permissions will be finalized in **AG-04 — Identity, Permissions & Auditability**.

---

## 4. Core V1 Objects

AssurGrid V1 will primarily track:

1. **Applications / Computerized Systems**
2. **Owners and responsible stakeholders**
3. **Periodic Reviews / PCRs**
4. **Audits**
5. **Audit findings**
6. **CAPAs / remediation actions**
7. **Changes**
8. **Validation activities**
9. **Recurring governance controls**
10. **Validation and lifecycle documents**
11. **Governance configuration / policies**
12. **Activity history and audit trail**

---

## 5. Three Independent Application States

A major AG-01 decision is that AssurGrid must not reduce an application to a single status badge.

Each application has at least three separate dimensions.

### 5.1 Lifecycle State

Example states:

- Implementation
- Operational
- Retirement
- Retired

These describe where the computerized system is in its lifecycle.

---

### 5.2 Validation State

Example states:

- Not Assessed
- Validation Required
- In Validation
- Validated
- Remediation Required

Validation state describes whether the system has appropriate documented evidence supporting its intended regulated use.

A system being **Validated** does not mean all of its governance activities are currently up to date.

---

### 5.3 Governance Health

Example states:

- Current
- Due Soon
- Overdue
- Critical Attention

Governance Health is derived from the application's applicable governance activities and their current status.

Example:

> **LIMS**  
> Lifecycle: Operational  
> Validation State: Validated  
> Governance Health: Overdue

This is valid because a system can remain validated while having an overdue periodic review or another governance obligation requiring attention.

---

## 6. Configurable Governance Model

Governance requirements must be configurable by appropriate authorized users.

Configuration may include:

- which controls apply,
- activity frequency,
- due-soon threshold,
- document requirements,
- review requirements,
- escalation rules,
- system classification rules,
- validation-impact rules,
- governance-health calculation rules,
- application-level exceptions or overrides.

These settings must not be freely editable by ordinary users.

---

## 7. Organization Defaults and Application Overrides

AssurGrid should support a hierarchy such as:

**Organization Policy → System Classification → Applicable Controls → Schedule → Actual Activities → Governance Health**

Example organization default:

### High-Criticality GxP Application

- Periodic Review: every 12 months
- Due Soon threshold: 30 days
- Access Review: every 3 months
- Audit Trail Review: every 3 months
- Supplier Review: every 24 months

An individual application may override an inherited rule where justified.

Example:

> Organization default ATR frequency: Quarterly  
> LIMS override: Monthly  
> Reason: Higher data-integrity risk

Application-specific overrides must require an authorized user and should capture a justification.

---

## 8. Auditability of Configuration Changes

Governance configuration is itself controlled information.

AssurGrid must preserve:

- who changed a rule,
- when it changed,
- previous value,
- new value,
- reason / justification,
- affected application or policy,
- historical versions.

An authorized user must not be able to make an overdue obligation disappear merely by changing its frequency without leaving a trace.

Example:

> PCR frequency changed from 12 months to 24 months.

AssurGrid should retain both the previous and new configuration and identify who changed it and why.

---

## 9. Due-Soon and Overdue Logic

AssurGrid should calculate activity status from configuration and actual activity data.

Example:

- Next due date: 31 October 2026
- Due Soon window: 30 days

Derived status:

- More than 30 days remaining → **Current**
- 1–30 days remaining → **Due Soon**
- Due date passed without approved completion → **Overdue**

The due-soon window must be configurable.

Users should not ordinarily manually select an item's status as Due Soon or Overdue; AssurGrid should derive it.

---

## 10. Governance Activities

Examples of activities AssurGrid may support include:

- Periodic Review / PCR
- Audit Trail Review
- Access Review
- Privileged Access Review
- Supplier Review / Reassessment
- Backup / Restore Testing
- Disaster Recovery Testing
- Security Review
- Risk Review
- Validation Review
- Audit
- CAPA / remediation
- Required document review
- Other organization-defined recurring controls

Not every control applies to every application.

Applicability and frequency should be policy-driven and risk-based.

---

## 11. Changes and Validation Impact

Changes must be tracked independently from validation state.

Example:

> LIMS is currently Validated.  
> A major upgrade is initiated.  
> The change has validation impact.  
> Regression testing and validation evidence are required.

The system should not automatically become “Unvalidated” simply because a controlled change is in progress.

Instead, AssurGrid should be capable of representing information such as:

- Validation State: Validated
- Active Change: Validation-impacting
- Validation work: In progress
- Evidence: Pending

Rules for when a system should move to **Remediation Required** or another validation state will be defined later.

---

## 12. Validation and Lifecycle Documents

AssurGrid must support controlled tracking of validation and lifecycle documents.

Initial examples include:

- Validation Plan (VP)
- Validation Report (VR)
- Test / Installation Plan (TIP)
- Test / Installation Report (TIR)
- Functional Risk Assessment (FRA)
- Audit Trail Review Determination
- POM
- GPOM
- Service Transition Plan (STP)
- Service Transition Report (STR)
- Data Transfer Plan (DTP)
- Data Transfer Report (DTR)
- Decommission Plan
- Decommission Report
- Risk Assessments
- other organization-defined document types

AssurGrid must **not** assume that these exact names or documents are universal.

Document types should therefore be configurable.

Document tracking should eventually support:

- document type,
- document identifier,
- version,
- status,
- effective / approval date,
- repository reference,
- owner,
- historical versions,
- related application,
- related change or validation activity where applicable.

Actual document-storage architecture will be decided in **AG-02**.

---

## 13. Application Registry

The application registry is one of the central product areas.

An application may include:

- application name,
- CI / system identifier,
- description,
- GxP classification,
- criticality,
- lifecycle state,
- validation state,
- governance health,
- business owner,
- technical owner,
- quality/governance owner,
- supplier,
- platform / hosting information,
- relevant dates,
- applicable governance profile,
- linked governance activities,
- linked documents,
- changes,
- audits,
- findings,
- CAPAs,
- activity history.

The final data model will be designed in AG-02 and implemented using knowledge from DBW.

---

## 14. Core Product Experience

AssurGrid should answer several questions quickly.

### Portfolio level

- What requires attention today?
- Which activities are overdue?
- Which activities are due soon?
- Which applications have governance concerns?
- Which findings or CAPAs remain open?
- Which important changes are active?
- Which applications require validation or remediation work?

### Application level

When opening an application, a user should be able to understand:

- what this system is,
- who owns it,
- its lifecycle state,
- its validation state,
- its governance health,
- its applicable controls,
- upcoming and overdue activities,
- recent changes,
- audits and findings,
- validation activity,
- documents,
- history.

---

## 15. UX Direction

The final interface should be:

- calm,
- clear,
- professional,
- low-noise,
- easy to scan,
- suitable for daily operational use,
- understandable without extensive training,
- capable of handling substantial governance information without becoming visually overwhelming.

The earlier UI comparison based mostly on color/style is discarded.

The next UI exploration should compare genuinely different product structures, such as:

1. **Workspace-first**
   - applications are the primary entry point.

2. **Governance command center**
   - attention, obligations, and upcoming work dominate the homepage.

3. **Registry-first**
   - the regulated-system inventory and structured records dominate the product.

A hybrid is allowed if testing shows that it better serves the product.

The UI direction should be selected using real AssurGrid governance data and rules rather than arbitrary sample status badges.

---

## 16. V1 Scope

V1 should focus on proving the core governance workflow.

Included:

- application registry,
- lifecycle / validation / governance states,
- ownership,
- governance-policy configuration,
- recurring governance activities,
- due-soon / overdue calculation,
- changes,
- audits,
- findings / CAPAs,
- validation activities,
- document metadata and history,
- user roles and permissions,
- auditability,
- portfolio and application-level views.

---

## 17. V1 Non-Goals

AssurGrid V1 is **not** intended to:

- replace ServiceNow,
- replace a full enterprise QMS,
- replace an electronic document-management system,
- execute laboratory or manufacturing processes,
- act as a document-authoring suite,
- replicate every pharmaceutical governance process,
- encode one company's SOPs as universal regulatory requirements,
- become a generic project-management tool,
- include features merely because other enterprise applications have them.

Every feature must serve a clear AssurGrid requirement.

---

## 18. Product Design Rule

> **Build only what the product needs. Understand and defend every major decision. Remove anything that has no clear product or engineering purpose.**

This principle governs the entire AssurGrid build.

---

## 19. Decisions Deferred to AG-02

The following are deliberately deferred to **AG-02 — System Design & Architecture**:

- final frontend architecture,
- formal confirmation of React/Vite or alternatives,
- frontend/backend boundaries,
- API architecture,
- PostgreSQL data model,
- authentication architecture,
- file/document storage architecture,
- audit-log technical design,
- notification architecture,
- deployment topology,
- environment strategy,
- integrations with external enterprise systems,
- architecture for organization defaults and application-level overrides.

---

## 20. Decisions Deferred to AG-04

The following are deliberately deferred to **AG-04 — Identity, Permissions & Auditability**:

- final role names,
- permission matrix,
- authentication flows,
- authorization rules,
- account lifecycle,
- privileged configuration permissions,
- audit-trail implementation details,
- approval requirements for sensitive configuration changes.

---

# AG-01 Outcome

AG-01 establishes AssurGrid as:

> **A configurable, auditable governance platform for regulated computerized systems that separates lifecycle state, validation state, and ongoing governance health, and derives operational status from organization-defined controls rather than arbitrary hardcoded rules.**

**AG-01 Status: LOCKED**

Next chapter:

# AG-02 — System Design & Architecture
