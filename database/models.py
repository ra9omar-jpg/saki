from datetime import datetime
from database.db import db


class TeamMember(db.Model):
    __tablename__ = "team_members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    whatsapp_number = db.Column(db.String(30), unique=True)
    teams_user_id = db.Column(db.String(120), unique=True)
    telegram_chat_id = db.Column(db.String(30), unique=True)
    team = db.Column(db.String(20), nullable=False)  # "marketing" or "rd"
    role = db.Column(db.String(50), default="member")
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship("Task", backref="assignee", lazy=True)
    poll_responses = db.relationship("PollResponse", backref="member", lazy=True)
    status_updates = db.relationship("StatusUpdate", backref="member", lazy=True)
    engagement_records = db.relationship("EngagementRecord", backref="member", lazy=True)

    def __repr__(self):
        return f"<TeamMember {self.name} ({self.team})>"


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    planner_id = db.Column(db.String(120), unique=True)
    title = db.Column(db.String(500), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("team_members.id"))
    status = db.Column(db.String(30), default="not_started")
    bucket = db.Column(db.String(120))
    due_date = db.Column(db.DateTime)
    planner_updated_at = db.Column(db.DateTime)
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan_id = db.Column(db.String(120))

    def __repr__(self):
        return f"<Task {self.title[:40]}>"


class Poll(db.Model):
    __tablename__ = "polls"
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date, nullable=False)
    question_text = db.Column(db.Text)
    platform = db.Column(db.String(20))
    group_id = db.Column(db.String(200))
    sent_at = db.Column(db.DateTime)
    closes_at = db.Column(db.DateTime)
    is_closed = db.Column(db.Boolean, default=False)
    reminder_sent_24h = db.Column(db.Boolean, default=False)
    reminder_sent_12h = db.Column(db.Boolean, default=False)

    responses = db.relationship("PollResponse", backref="poll", lazy=True)


class PollResponse(db.Model):
    __tablename__ = "poll_responses"
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("team_members.id"), nullable=False)
    response_text = db.Column(db.Text)
    responded_at = db.Column(db.DateTime, default=datetime.utcnow)


class StatusUpdate(db.Model):
    __tablename__ = "status_updates"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("team_members.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))
    status_text = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    week_of = db.Column(db.Date)

    task = db.relationship("Task")


class ArticleReview(db.Model):
    __tablename__ = "article_reviews"
    id = db.Column(db.Integer, primary_key=True)
    planner_task_id = db.Column(db.String(120), unique=True)
    title = db.Column(db.String(500))
    article_link = db.Column(db.String(1000))
    claimed_by_id = db.Column(db.Integer, db.ForeignKey("team_members.id"))
    claimed_at = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    feedback_text = db.Column(db.Text)
    status = db.Column(db.String(30), default="waiting")
    week_requested = db.Column(db.Date)
    reminder_sent = db.Column(db.Boolean, default=False)
    unclaimed_ping_count = db.Column(db.Integer, default=0)

    claimed_by = db.relationship("TeamMember")


class OutgoingMessage(db.Model):
    __tablename__ = "outgoing_messages"
    id = db.Column(db.Integer, primary_key=True)
    message_type = db.Column(db.String(60))
    platform = db.Column(db.String(20))
    recipient_type = db.Column(db.String(20))
    recipient_id = db.Column(db.String(200))
    content = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    approved_by_rani_at = db.Column(db.DateTime)
    is_approved = db.Column(db.Boolean, default=False)
    rani_confirmation_id = db.Column(db.Integer, db.ForeignKey("rani_confirmations.id"))


class IncomingMessage(db.Model):
    __tablename__ = "incoming_messages"
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20))
    group_id = db.Column(db.String(200))
    sender_whatsapp = db.Column(db.String(30))
    sender_teams_id = db.Column(db.String(120))
    sender_telegram_id = db.Column(db.String(30))
    content = db.Column(db.Text)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_question = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime)
    reminder_sent_at = db.Column(db.DateTime)   # ONE reminder sent (Function 13)
    escalated_to_rani_at = db.Column(db.DateTime)
    tagged_expert_at = db.Column(db.DateTime)


class EngagementRecord(db.Model):
    __tablename__ = "engagement_records"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("team_members.id"), nullable=False)
    week_of = db.Column(db.Date, nullable=False)
    poll_responded = db.Column(db.Boolean, default=False)
    status_update_responded = db.Column(db.Boolean, default=False)
    workshop_attended = db.Column(db.Boolean, default=False)
    messages_sent_count = db.Column(db.Integer, default=0)
    articles_claimed = db.Column(db.Integer, default=0)
    articles_completed = db.Column(db.Integer, default=0)


class WorkshopSession(db.Model):
    __tablename__ = "workshop_sessions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    team = db.Column(db.String(20))
    opening_recorded_at = db.Column(db.DateTime)
    closing_recorded_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    summary_approved = db.Column(db.Boolean, default=False)
    summary_text = db.Column(db.Text)

    marketing_tasks = db.relationship("MarketingTaskRecord", backref="session", lazy=True)


class MarketingTaskRecord(db.Model):
    __tablename__ = "marketing_task_records"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("workshop_sessions.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("team_members.id"), nullable=False)
    task_description = db.Column(db.Text)
    assigned_at_opening = db.Column(db.DateTime)
    delivered_at_closing = db.Column(db.DateTime)
    was_delivered = db.Column(db.Boolean)
    claimed_week_independent = db.Column(db.Boolean, default=False)

    member = db.relationship("TeamMember")


class RaniConfirmation(db.Model):
    __tablename__ = "rani_confirmations"
    id = db.Column(db.Integer, primary_key=True)
    message_type = db.Column(db.String(60))
    description = db.Column(db.Text)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    scheduled_time = db.Column(db.DateTime)
    is_sent = db.Column(db.Boolean, default=False)
    pending_message_id = db.Column(db.Integer)


class MediaWorkshopDraft(db.Model):
    """Holds a workshop summary generated from audio/image/text sent by Rani."""
    __tablename__ = "media_workshop_drafts"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_materials_json = db.Column(db.Text)   # JSON list of transcribed/extracted texts
    summary_text = db.Column(db.Text)
    status = db.Column(db.String(30), default="awaiting_group_selection")
    # "awaiting_group_selection", "sent"
    selected_groups_json = db.Column(db.Text)  # JSON list of group codes


class SakiState(db.Model):
    """Global runtime state — only one row ever exists (id=1)."""
    __tablename__ = "saki_state"
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(20), default="test")  # "test", "shadow", "live"
    is_paused = db.Column(db.Boolean, default=False)
    paused_until = db.Column(db.DateTime)
    is_shutdown = db.Column(db.Boolean, default=False)
    islamic_reminders_enabled = db.Column(db.Boolean, default=True)
    paused_groups_json = db.Column(db.Text, default="[]")
    rani_command_mode_until = db.Column(db.DateTime)


def get_saki_state() -> SakiState:
    state = SakiState.query.get(1)
    if not state:
        state = SakiState(id=1)
        db.session.add(state)
        db.session.commit()
    return state
