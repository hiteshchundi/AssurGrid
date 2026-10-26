# AG-00 — AssurGrid Product Philosophy

**Status:** Locked  
**Project:** AssurGrid  
**Purpose:** Define why AssurGrid exists, what problem it solves, the principles that guide it, and the boundaries of the product before detailed product design begins.

---

## 1. Product Origin

AssurGrid is based on a real operational problem observed while providing quality oversight for a regulated application estate.

Information about regulated applications and their activities was fragmented across multiple systems, repositories, spreadsheets, project teams, and individual knowledge.

Examples included:

- Periodic Compliance Review (PCR) schedules
- Audit dates
- Audit finding closure deadlines
- Change activity
- Successful and unsuccessful changes
- Application ownership
- Validation documentation
- Operational documentation
- Historical document versions
- Application-specific quality and compliance information

For quality oversight teams, there was no single accessible place that clearly answered questions such as:

- Which applications have PCRs due soon?
- Which applications have overdue PCRs?
- Which applications are approaching an audit?
- Which audit findings are approaching their closure deadline?
- Which findings are already overdue?
- How many normal changes has an application performed in the last six months?
- How many of those changes succeeded?
- How many failed?
- Which controlled documents exist for an application?
- Which document versions are current?
- Which historical versions existed previously?
- Which expected documents are missing?
- Where is the evidence stored?

In practice, information often had to be assembled manually.

A typical flow could look like:

```text
Project Team
     ↓
Obtain CI ID
     ↓
ServiceNow
     ↓
Export Excel
     ↓
Project-maintained spreadsheets
     ↓
VQD / GCMS document references
     ↓
Emails / Meetings / Individual Knowledge
     ↓
Manual Consolidation
     ↓
Answer
```

The problem was therefore not necessarily the absence of information.

The problem was the absence of a **shared, accessible and continuously updated operational picture**.

---

## 2. Product Vision

AssurGrid is a proactive oversight platform for regulated applications.

Its purpose is to bring together:

- Application information
- Compliance obligations
- Operational activities
- Quality events
- Controlled-document information
- Historical records
- Deadlines
- Trends
- Exceptions
- Evidence references

into one unified product.

AssurGrid should allow someone responsible for regulated applications to quickly understand:

> **What exists, what changed, what is due, what is missing, where the evidence is, and what requires attention.**

---

## 3. North Star

> **AssurGrid gives teams a unified, time-aware and historically traceable view of regulated applications—their compliance obligations, operational activity, controlled-document landscape and significant events—while integrating with the systems where that information originates.**

The primary question AssurGrid should answer is:

> **What does someone responsible for regulated applications need to know today?**

---

## 4. Product Thesis

A quality professional responsible for a portfolio of regulated applications should be able to open AssurGrid and, within a few minutes, understand:

- What applications they oversee
- What compliance activities are approaching
- What activities are overdue
- What important operational activity has occurred
- What controlled documentation exists
- What documentation is missing or potentially outdated
- Where evidence is stored
- What has changed historically
- Where their attention is required

---

## 5. AssurGrid Is an Oversight System

AssurGrid does not need to perform every regulated activity itself.

For example:

- Changes may still be executed in ServiceNow.
- Controlled documents may remain in approved document repositories.
- Audit findings may originate in a quality-management system.
- Validation execution may occur in another validated platform.

AssurGrid sits above these systems and provides a consolidated operational and compliance view.

```text
                  ASSURGRID
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
   Application    Compliance     Operational
    Registry       Activities      Activity
       │              │              │
       │          PCR / Audits      Changes
       │          Findings          Incidents
       │          Reviews           Releases
       │              │              │
       └──────────────┼──────────────┘
                      │
                Oversight View
                      │
            Alerts • Trends • Risk
```

AssurGrid should therefore be understood primarily as a:

> **System of visibility and oversight**

rather than automatically becoming the system of record for every activity it displays.

---

## 6. One Application, One Operational Home

A regulated application may have information scattered across:

- ServiceNow
- Validation repositories
- Controlled-document repositories
- Quality systems
- Project spreadsheets
- Emails
- Meetings
- Local trackers
- Individual team knowledge

AssurGrid should provide one operational home from which the application can be understood.

Conceptually:

```text
Application
│
├── Overview
├── Obligations
│   ├── Periodic Compliance Review
│   ├── Audit Activities
│   └── Required Reviews
├── Changes
├── Documents
│   ├── Validation
│   ├── Requirements
│   ├── Risk
│   ├── Testing
│   ├── Operations
│   ├── Access / Security
│   ├── Data Transfer
│   ├── Service Transition
│   ├── Disaster Recovery
│   └── Retirement
├── Audit Findings
├── Timeline
└── Administration
```

The application page should become the canonical place from which users understand the application's current state.

It does **not** necessarily need to become the authoritative storage location for every underlying record.

---

## 7. Proactive Rather Than Reactive

Traditional tracking often behaves like:

```text
Something becomes due
        ↓
Someone notices
        ↓
Someone sends an email
        ↓
People react
```

AssurGrid should reverse this:

```text
System knows obligation
        ↓
System knows due date
        ↓
System monitors approaching date
        ↓
System surfaces it automatically
        ↓
Responsible people act
        ↓
System records completion
```

Users should not be expected to remember every compliance deadline.

> **AssurGrid should remember for them.**

Examples may include:

- Upcoming PCR
- Due-soon PCR
- Overdue PCR
- Upcoming audit
- Audit finding approaching closure deadline
- Overdue audit finding
- Document review due
- Required review approaching
- Other time-based regulated activities

Exact alert thresholds should be configurable rather than permanently hard-coded.

---

## 8. Time Is a First-Class Product Concept

Many of AssurGrid's most important questions involve time:

- Due next month
- Due within 90 days
- Overdue
- Last six months
- Last PCR
- Next PCR
- Open for 45 days
- Deadline extended
- Review completed late
- No activity for a defined period
- Change activity trends

Dates should therefore not exist merely as passive fields inside forms.

They should drive product behaviour.

AssurGrid should actively understand concepts such as:

- Planned date
- Due date
- Completion date
- Age
- Time remaining
- Overdue duration
- Escalation level
- Historical effective period

---

## 9. Documentation Governance

Controlled documentation is a first-class part of the regulated application's history.

A validated computerized system may have documents such as:

- Periodic Compliance Review (PCR)
- Validation Plan
- Validation Report / Validation Summary Report
- Technical Installation Plan (TIP)
- Technical Installation Report / Record (TIR)
- Risk Assessment
- Functional Risk Assessment
- Audit Trail Review / Audit Trail Review Determination
- GxP Plan & Operations Manual (GPOM)
- Plan & Operations Manual (POM)
- Service Transition Plan
- Service Transition Report
- Data Transfer Plan
- Data Transfer Report
- Decommission Plan
- Decommission Report
- Requirements documentation
- Testing documentation
- Access / security documentation
- Disaster recovery documentation
- Change documentation
- Other lifecycle and operational documents required by the organization's procedures

> The exact controlled-document taxonomy should be aligned to the final DTMS document list when the domain model is formalized.

Historically, these documents may be distributed across repositories such as VQD and GCMS, with access restricted to application teams.

Quality oversight personnel may only be able to view a document after receiving its repository ID or reference from the application team.

This creates several problems:

- Poor discoverability
- Dependence on individual teams
- Difficulty determining whether required documentation exists
- Difficulty identifying the current version
- Incomplete historical version chains
- Poor traceability across the application's lifecycle
- Increased audit-preparation effort

AssurGrid should make documentation governance visible at the application level.

---

## 10. Document Lineage

Current documents alone are insufficient.

AssurGrid should preserve or reference the known history of each controlled document.

Example:

```text
Validation Plan

Version 1.0    Initial Validation
Version 2.0    Major Enhancement
Version 3.0    Infrastructure Migration
Version 4.0    Regulatory Update
Version 5.0    Major Release
Version 6.0    Cloud Migration
Version 7.0    Current
```

For each known document version, AssurGrid may eventually track metadata such as:

- Document type
- Document title
- Version
- Repository
- Repository document ID
- Status
- Effective date
- Superseded date
- Owner
- Approval information
- Reason for revision
- Related change
- Related lifecycle event
- Source link
- Previous version
- Next version

This supports questions such as:

> Which Validation Plan was effective when a particular change was implemented?

or:

> What was the documented validated state of this application at a particular point in time?

---

## 11. AssurGrid Is Not Necessarily the Document Repository

For the initial product direction, AssurGrid should not automatically attempt to replace validated document repositories.

If VQD, GCMS or another approved system remains the authoritative repository, AssurGrid can instead act as the:

> **Documentation index and governance layer**

AssurGrid may know:

- What the document is
- Which application it belongs to
- Which version is current
- Which historical versions are known
- Where it is stored
- Its repository ID
- Its effective period
- Its status
- Its related activity
- Its source link

while the actual controlled file continues to reside in the authorized repository.

---

## 12. Documentation Completeness

AssurGrid should eventually help quality teams identify documentation gaps.

Example:

```text
DOCUMENTATION COMPLETENESS

Expected documents:       18
Current:                  15
Missing:                   1
Potentially outdated:      2
```

The product should not automatically claim that an application is compliant simply because all expected items appear present.

Better wording includes:

- Expected document not identified
- Current version not confirmed
- Review due
- Potentially outdated
- Repository reference missing
- Historical version chain incomplete

AssurGrid supports oversight and judgment; it does not replace accountable quality decisions.

---

## 13. Portfolio → Application → Activity → Evidence

AssurGrid should support progressive drill-down.

### Level 1 — Portfolio

Answers:

> Where should I look?

Examples:

- PCRs due soon
- Overdue PCRs
- Open findings
- Findings due soon
- Overdue findings
- Recent change failure trends
- Applications with missing information

### Level 2 — Application

Answers:

> What is happening with this application?

Examples:

- Classification
- Owners
- Next PCR
- Open findings
- Change history
- Document status
- Current risks
- Upcoming obligations

### Level 3 — Activity

Answers:

> What produced this number or status?

Examples:

- Individual change records
- Individual findings
- Individual PCR
- Specific document version

### Level 4 — Evidence

Answers:

> Where is the supporting information?

Examples:

- Source repository
- Source record
- Document reference
- Historical version
- Related event
- Supporting metadata

Conceptually:

```text
Portfolio
    ↓
Application
    ↓
Activity
    ↓
Evidence
```

---

## 14. Dashboard Philosophy

AssurGrid should not create metrics merely because the data exists.

Every metric should support an operational question, decision or action.

Useful examples:

- Which PCRs are due in the next 30/60/90 days?
- Which applications have overdue findings?
- Which applications have unusually high unsuccessful-change rates?
- Which applications lack an assigned owner?
- Which expected documents cannot currently be identified?
- Which controlled documents are approaching review?

A number without a meaningful action or question should be challenged before being added to the product.

---

## 15. Notifications

Notifications are part of the product's core value, but alert fatigue must be treated as a design problem.

AssurGrid should notify users based on actionable urgency rather than simply because an event exists.

Possible notification mechanisms may eventually include:

- In-app notification
- Email
- Daily digest
- Weekly digest
- Immediate alert
- Escalation

Possible triggers may include:

- 90 days before due date
- 60 days before due date
- 30 days before due date
- 14 days before due date
- 7 days before due date
- Overdue
- Significant status change
- New critical finding
- Failed synchronization
- Missing required information

Exact thresholds should be configurable.

---

## 16. Historical Truth

AssurGrid should not simply overwrite the past.

For important regulated information, the product should be able to preserve history.

Examples:

- Previous application owner
- Previous due date
- Previous classification
- Previous document version
- Previous review status
- Deadline extensions
- Change history
- Status transitions

Questions AssurGrid should eventually support include:

- Who owned this application at a given point in time?
- When was a due date changed?
- Who changed it?
- Why was it changed?
- What was the previous value?
- Which document version was effective on a particular date?

AssurGrid is therefore both:

1. A live oversight platform
2. A historical record of regulated-application governance

---

## 17. External-System Integration

If AssurGrid eventually becomes a real product, data should flow into it from enterprise systems wherever possible.

The preferred model is:

```text
External Systems
      │
      ▼
Integration / Ingestion Layer
      │
      ▼
AssurGrid Unified Model
      │
      ▼
Oversight Experience
```

Potential source systems may include:

- ServiceNow
- CMDB
- VQD
- GCMS
- QMS platforms
- Validation systems
- Audit systems
- Document-management systems
- Other enterprise repositories

---

## 18. Integration Methods

AssurGrid should support multiple ingestion patterns.

### 18.1 API Integration

Where the source system provides APIs, AssurGrid can directly retrieve structured data.

Example:

```text
ServiceNow
    ↓ API
AssurGrid
```

This could provide:

- Change records
- CI information
- Status
- Implementation dates
- Change outcomes
- Related metadata

---

### 18.2 Scheduled Synchronization

AssurGrid may periodically ask source systems for new or changed records.

Example:

```text
Every defined interval

AssurGrid
    ↓
"Give me everything changed since the last successful sync."
```

This introduces future engineering concerns such as:

- Retry handling
- Synchronization state
- Idempotency
- Reconciliation
- Authentication
- Rate limiting
- Failure monitoring

---

### 18.3 Event-Driven Integration

Where supported, source systems may notify AssurGrid when an event occurs.

Example:

```text
Change closed
     ↓
Webhook / Event
     ↓
AssurGrid
     ↓
Update activity
     ↓
Recalculate metrics
     ↓
Refresh oversight view
```

---

### 18.4 File Import

Many enterprise environments still depend on structured exports.

AssurGrid should therefore support import patterns such as:

- CSV
- Excel
- JSON
- XML

Example:

```text
ServiceNow Export
      ↓
AssurGrid Importer
      ↓
Validate
      ↓
Match Application / CI
      ↓
Detect Duplicates
      ↓
Import
      ↓
Reconcile
      ↓
Update Dashboard
```

This is particularly suitable for the portfolio version because it can realistically simulate enterprise integrations.

---

### 18.5 Manual Entry

Not all data will originate in another system.

Some information may still need to be maintained by authorized users.

Examples:

- Next PCR due date
- Application owner
- Quality contact
- GxP classification
- Repository document reference
- Audit date
- Finding closure commitment date

AssurGrid should support both automated and controlled manual data entry.

---

## 19. Application Identity and Entity Mapping

The same application may be represented differently across multiple systems.

Example:

```text
ServiceNow:
GSK-CS-SAFETY-01

Document Repository:
Clinical Safety System

Another Repository:
CSS Global

Project Tracker:
Safety Platform
```

AssurGrid must understand that these references represent the same application.

A conceptual application identity may therefore include:

```text
AssurGrid ID
APP-000127

Application Name
Clinical Safety Platform

ServiceNow CI
CI-782819

CMDB ID
...

VQD Product ID
...

GCMS Product ID
...
```

This creates an important future capability:

> **Entity mapping / identity resolution**

Reliable cross-system identity will be essential for trustworthy integrations.

---

## 20. Data Provenance

Externally sourced data should retain its origin.

If AssurGrid shows:

```text
Normal Changes: 31
```

the user should eventually be able to see information such as:

```text
Source: ServiceNow
Last synchronized: 26-Sep-2026 10:42
```

If a PCR due date was manually maintained:

```text
Source: Manual
Updated by: Quality User
Updated: 19-Aug-2026
```

Provenance increases trust and makes discrepancies easier to investigate.

---

## 21. Portfolio Version Strategy

The portfolio version should simulate real enterprise integrations rather than hard-coding every dashboard number.

Example:

```text
mock-data/
├── application_registry.csv
├── servicenow_changes.csv
├── audit_findings.csv
└── document_repository.csv
```

A realistic flow could be:

```text
ServiceNow-like CSV
       ↓
AssurGrid Import
       ↓
Match CI IDs
       ↓
Store Activities
       ↓
Calculate Metrics
       ↓
Dashboard
```

This makes the portfolio project more realistic and more defensible during technical review.

---

## 22. What AssurGrid Is Not

For the initial product direction, AssurGrid is not intended to be:

- A ServiceNow replacement
- A full Quality Management System
- A complete electronic document-management system
- A validation execution platform
- A test-management suite
- A generic CAPA platform
- A generic project-management tool
- A dashboard with no operational meaning

It is:

> **A regulated-application oversight platform that unifies visibility, deadlines, controlled-document information, historical traceability, activity and evidence across the application estate.**

---

## 23. Product Principles

### P1 — One application, one operational home.

All important information about a regulated application should be discoverable from a single application view.

### P2 — Surface what needs attention before users have to search for it.

AssurGrid should proactively expose upcoming, due-soon and overdue activities.

### P3 — Integrate without unnecessarily replacing authoritative systems.

Existing validated systems may continue to own the underlying records.

### P4 — Every metric must support a decision or action.

Avoid decorative dashboards.

### P5 — Support drill-down from summary to evidence.

Users should be able to move from portfolio → application → activity → evidence.

### P6 — Time, deadlines and ageing are first-class concepts.

Dates should drive behaviour, not merely exist as fields.

### P7 — Preserve history rather than overwriting the past.

Historical truth matters in regulated environments.

### P8 — Notifications should prioritize action without creating alert fatigue.

Alerting must be meaningful and configurable.

### P9 — Human accountability remains essential.

AssurGrid supports quality oversight but does not replace accountable compliance judgment.

### P10 — Reduce spreadsheet dependence without rebuilding spreadsheets in a browser.

The product should understand regulated concepts rather than merely display rows and columns.

### P11 — Integrate with enterprise systems so users do not repeatedly reproduce information that already exists elsewhere.

APIs, scheduled synchronization, events, file imports and controlled manual entry should all be supported where appropriate.

### P12 — Document lineage is part of the regulated application's history.

Current documents alone are insufficient.

### P13 — Externally sourced data should retain provenance.

Users should understand where information came from and when it was last updated.

---

## 24. Guiding Product Question

Every significant feature should ultimately help answer:

> **For this regulated application, what exists, what changed, what is due, what is missing, where is the evidence, and what requires attention?**

If a feature does not meaningfully contribute to answering that question, its inclusion should be challenged.

---

## 25. AG-00 Decision

The following direction is now locked:

> **AssurGrid is a proactive regulated-application oversight platform. It consolidates application information, compliance obligations, operational activity, controlled-document metadata, historical document lineage, deadlines, events and evidence references into a unified operational view. It should integrate with authoritative enterprise systems rather than unnecessarily replacing them, preserve history, retain data provenance, and proactively surface what requires attention.**

Detailed workflows, actors, domain objects, screen structure, statuses, lifecycle rules and V1 boundaries will be defined in **AG-01 — Product Design**.
