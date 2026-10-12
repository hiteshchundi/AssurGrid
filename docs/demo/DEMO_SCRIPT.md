# Current AssurGrid demonstration

## Available through Slice 02

1. Follow the root README to start PostgreSQL, apply migrations, and start FastAPI and Vite.
2. Open `http://localhost:5173`. The foundation page should show API and Database **Connected**. This is the only application screen available.
3. Run `alembic -c backend/alembic.ini current` from the repository root with the backend environment activated. Expect `0002_application_registry (head)`.
4. Run the opt-in PostgreSQL integration-test command in the README. It demonstrates inserting and reading fictional application data, rejecting duplicate CIs within one organization, rejecting invalid relationships/states, and preserving independent lifecycle and validation values.

The tests use temporary synthetic records, not a seeded estate. They leave no demo records in the development database. There is no registry screen, login, policy calculation, or QA workflow to demonstrate yet.

## Intended story for later slices

Open a synthetic application that is Operational and Validated, then explain its Overdue governance health by drilling into the concrete PCR deadline, applied policy version, and evidence. Follow an implemented change through owner submission, separate QA review, closure, and visibly simulated outbound delivery. These steps are planned and must not be presented as working until their slices pass verification.
