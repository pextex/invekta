"""Add tasks, activities, in-app reminders and immutable work history."""

from alembic import op
import sqlalchemy as sa

revision = "b273e4f50612"
down_revision = "a162bced9031"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "unique_opportunity_company_unit",
        "opportunities",
        ["id", "company_id", "business_unit_id"],
    )
    op.execute("""
CREATE TABLE tasks (
	status VARCHAR(20) DEFAULT 'open' NOT NULL,
	priority VARCHAR(20) DEFAULT 'normal' NOT NULL,
	due_at TIMESTAMP WITH TIME ZONE NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE,
	id SERIAL NOT NULL,
	business_unit_id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	opportunity_id INTEGER,
	assignee_id INTEGER NOT NULL,
	creator_id INTEGER NOT NULL,
	title VARCHAR(200) NOT NULL,
	notes TEXT,
	remind_at TIMESTAMP WITH TIME ZONE,
	version INTEGER DEFAULT '1' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	archived_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(business_unit_id) REFERENCES business_units (id),
	FOREIGN KEY(company_id, business_unit_id) REFERENCES companies (id, business_unit_id),
	FOREIGN KEY(opportunity_id, company_id, business_unit_id) REFERENCES opportunities (id, company_id, business_unit_id),
	FOREIGN KEY(assignee_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	FOREIGN KEY(creator_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	CONSTRAINT unique_task_id_unit UNIQUE (id, business_unit_id),
	CONSTRAINT positive_task_version CHECK (version >= 1),
	CONSTRAINT valid_task_status CHECK (status IN ('open','doing','done','cancelled')),
	CONSTRAINT valid_task_priority CHECK (priority IN ('low','normal','high')),
	CONSTRAINT task_completion_consistent CHECK ((status='done') = (completed_at IS NOT NULL))
)
    """)
    op.execute("CREATE INDEX ix_task_company ON tasks (company_id)")
    op.execute("CREATE INDEX ix_task_due ON tasks (business_unit_id, status, due_at)")
    op.execute(
        "CREATE INDEX ix_task_unit_assignee ON tasks (business_unit_id, assignee_id)"
    )
    op.execute("""
CREATE TABLE activities (
	kind VARCHAR(20) NOT NULL,
	status VARCHAR(20) DEFAULT 'planned' NOT NULL,
	scheduled_at TIMESTAMP WITH TIME ZONE,
	occurred_at TIMESTAMP WITH TIME ZONE,
	outcome TEXT,
	id SERIAL NOT NULL,
	business_unit_id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	opportunity_id INTEGER,
	assignee_id INTEGER NOT NULL,
	creator_id INTEGER NOT NULL,
	title VARCHAR(200) NOT NULL,
	notes TEXT,
	remind_at TIMESTAMP WITH TIME ZONE,
	version INTEGER DEFAULT '1' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	archived_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(business_unit_id) REFERENCES business_units (id),
	FOREIGN KEY(company_id, business_unit_id) REFERENCES companies (id, business_unit_id),
	FOREIGN KEY(opportunity_id, company_id, business_unit_id) REFERENCES opportunities (id, company_id, business_unit_id),
	FOREIGN KEY(assignee_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	FOREIGN KEY(creator_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	CONSTRAINT unique_activity_id_unit UNIQUE (id, business_unit_id),
	CONSTRAINT positive_activity_version CHECK (version >= 1),
	CONSTRAINT valid_activity_status CHECK (status IN ('planned','done','cancelled')),
	CONSTRAINT valid_activity_kind CHECK (kind IN ('call','meeting','note')),
	CONSTRAINT activity_schedule_required CHECK (status!='planned' OR scheduled_at IS NOT NULL),
	CONSTRAINT activity_completion_consistent CHECK ((status='done') = (occurred_at IS NOT NULL))
)
    """)
    op.execute("CREATE INDEX ix_activity_company ON activities (company_id)")
    op.execute(
        "CREATE INDEX ix_activity_schedule ON activities (business_unit_id, status, scheduled_at)"
    )
    op.execute(
        "CREATE INDEX ix_activity_unit_assignee ON activities (business_unit_id, assignee_id)"
    )
    op.execute("""
CREATE TABLE reminders (
	id SERIAL NOT NULL,
	business_unit_id INTEGER NOT NULL,
	task_id INTEGER,
	activity_id INTEGER,
	recipient_id INTEGER NOT NULL,
	fire_at TIMESTAMP WITH TIME ZONE NOT NULL,
	status VARCHAR(20) DEFAULT 'pending' NOT NULL,
	delivered_at TIMESTAMP WITH TIME ZONE,
	read_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(task_id, business_unit_id) REFERENCES tasks (id, business_unit_id),
	FOREIGN KEY(activity_id, business_unit_id) REFERENCES activities (id, business_unit_id),
	CONSTRAINT one_reminder_context CHECK ((task_id IS NULL) != (activity_id IS NULL)),
	FOREIGN KEY(recipient_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	CONSTRAINT valid_reminder_status CHECK (status IN ('pending','delivered','cancelled')),
	CONSTRAINT reminder_read_delivered CHECK (read_at IS NULL OR status='delivered')
)
    """)
    op.execute("CREATE INDEX ix_reminder_due ON reminders (status, fire_at)")
    op.execute(
        "CREATE INDEX ix_reminder_recipient ON reminders (business_unit_id, recipient_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX unique_activity_pending_reminder ON reminders (activity_id) WHERE status = 'pending'"
    )
    op.execute(
        "CREATE UNIQUE INDEX unique_task_pending_reminder ON reminders (task_id) WHERE status = 'pending'"
    )
    op.execute("""
CREATE TABLE work_events (
	id SERIAL NOT NULL,
	business_unit_id INTEGER NOT NULL,
	task_id INTEGER,
	activity_id INTEGER,
	actor_id INTEGER NOT NULL,
	action VARCHAR(20) NOT NULL,
	changes JSONB NOT NULL,
	changed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(task_id, business_unit_id) REFERENCES tasks (id, business_unit_id),
	FOREIGN KEY(activity_id, business_unit_id) REFERENCES activities (id, business_unit_id),
	FOREIGN KEY(actor_id, business_unit_id) REFERENCES memberships (user_id, business_unit_id),
	CONSTRAINT one_work_event_context CHECK ((task_id IS NULL) != (activity_id IS NULL))
)
    """)
    op.execute("CREATE INDEX ix_work_event_activity ON work_events (activity_id, id)")
    op.execute("CREATE INDEX ix_work_event_task ON work_events (task_id, id)")


def downgrade():
    # Hold locks until rollback/commit so a concurrent write cannot be dropped.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "LOCK TABLE tasks, activities, reminders, work_events IN ACCESS EXCLUSIVE MODE"
        )
    )
    populated = bind.scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM tasks) OR EXISTS(SELECT 1 FROM activities) OR EXISTS(SELECT 1 FROM reminders) OR EXISTS(SELECT 1 FROM work_events)"
        )
    )
    if populated:
        raise RuntimeError(
            "Downgrade refused: work records must be preserved. Restore application code or use a reviewed backup plan."
        )
    op.drop_table("work_events")
    op.drop_table("reminders")
    op.drop_table("activities")
    op.drop_table("tasks")
    op.drop_constraint(
        "unique_opportunity_company_unit", "opportunities", type_="unique"
    )
