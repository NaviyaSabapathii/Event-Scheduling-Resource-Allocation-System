from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    allocations = db.relationship('EventResourceAllocation', backref='event', cascade="all, delete-orphan")

class Resource(db.Model):
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    allocations = db.relationship('EventResourceAllocation', backref='resource', cascade="all, delete-orphan")

class EventResourceAllocation(db.Model):
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.resource_id'), nullable=False)