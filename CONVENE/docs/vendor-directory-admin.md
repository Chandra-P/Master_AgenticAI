# Where approved vendors are stored

The React website's `/api/vendors` reads the **PostgreSQL development database**.
It no longer assigns approval labels from Python code or silently falls back to
the static catalog. The existing three venues and two decorators were imported.
Food has no approved records yet.

| Table | Contents |
|---|---|
| `vendor_records` | Stable vendor ID, latest draft version, publication pointer, active/suspended status |
| `vendor_versions` | Immutable complete vendor snapshot, contact details, source evidence, SHA-256 content hash, creator label and creation time |
| `vendor_approval_history` | Immutable approve/suspend decision, exact vendor version and hash, reviewer provenance, effective approval date, recording time and reason |

An approval points to an exact version. Editing creates a draft; the last approved
version remains published until a reviewer approves the new head version. A stale
approval is rejected. Suspension removes the record from current directory reads
without deleting history or cancelling anything. Frontend reopening refetches
the directory instead of retaining stale approvals indefinitely.

The initial five approvals explicitly say **project-owner (conversation approval)**,
effective November 1, 2026, based on the user's confirmation of the existing list.
Their import/recording times are separate. This is not a fabricated Google login
or a new review of every source fact. Local operator labels are audit labels;
authenticated reviewer identity and a web admin UI remain future work.

## Local database roles

`convene_app` can SELECT published directory data and cannot insert or modify
directory tables. RLS hides drafts and unpublished audit records. Setting the old
administrative flag cannot grant access. `convene_directory_admin` is a separate
non-superuser login, not a role membership of the website login. Its CLI can
append versions/decisions and update publication status. There are no public
directory write/approval endpoints.

Credentials live only in ignored local files. For a hosted service, give the web
runtime only its normal database secret; give directory credentials only to the
administrative operator environment. The shared local `.env` is a development
convenience, not a production secret-distribution design.

## First local setup

The existing workspace has already completed these steps. On a fresh workspace,
initialize the local PostgreSQL databases, then apply schema migrations **before**
transferring the directory tables to their dedicated owner:

```powershell
.venv/Scripts/python.exe scripts/init_planner_db.py
.venv/Scripts/python.exe scripts/init_planner_db.py --test
.venv/Scripts/python.exe scripts/setup_directory_roles.py
.venv/Scripts/python.exe scripts/vendor_directory.py --operator "local project owner" import-existing
```

The local-only role helper targets `convene_dev` and `convene_test` on
127.0.0.1:55432, reads the existing ignored PostgreSQL administrator password,
and stores a separate randomized directory password and admin URLs without
printing credentials. It creates no cloud resource or Windows service.

Repeated import skips any existing vendor ID, including changed, draft or
suspended records. It cannot reset an edited record to a Python default or
silently reapprove a suspended vendor. `party_catalog.py` remains only the
legacy/demo data and explicit initial-import input.

Future migrations that alter these directory tables must be run with their
schema-administration authority; the website credential cannot alter admin-owned
tables. Apply migrations in deployment administration, never from HTTP requests.

## Reviewing and publishing

Read all versions, their sources and approval history:

```powershell
.venv/Scripts/python.exe scripts/vendor_directory.py --operator "reviewer label" history south-san
```

The following are examples of operator actions, not commands run automatically:

```powershell
# vendor-draft.json contains the complete public vendor details, not approval metadata.
.venv/Scripts/python.exe scripts/vendor_directory.py --operator "reviewer label" draft --file vendor-draft.json --expected-version 1 --reason "Updated published details"
.venv/Scripts/python.exe scripts/vendor_directory.py --operator "reviewer label" approve south-san --version 2 --reason "Reviewed version 2 and its sources"
.venv/Scripts/python.exe scripts/vendor_directory.py --operator "reviewer label" suspend south-san --reason "Contact details need review"
```

Approval is for directory use, never confirmation of event availability, final
price, reservation, contract or payment. A verified email remains required before
Gmail outreach; currently the venue phone/official page are verified but direct
email is unknown.

The legacy local demo on port 8000 still uses its static fixtures. The React
planner on port 8001 uses the database-backed directory for confirmed-brief
recommendations and approved-provider RAG. See [the planner flow](approved-catalog-planner.md).
