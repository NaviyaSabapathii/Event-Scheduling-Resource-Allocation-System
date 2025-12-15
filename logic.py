from models import EventResourceAllocation, Event

def is_resource_conflicting(resource_id, start_time, end_time, ignore_event_id=None):
    if start_time >= end_time:
        return True, "Error: End time must be after start time." [cite: 36]

    allocations = EventResourceAllocation.query.filter_by(resource_id=resource_id).all()
    
    for alloc in allocations:
        # Important for editing: ignore the current event's own time slot
        if ignore_event_id and alloc.event_id == ignore_event_id:
            continue
            
        other = Event.query.get(alloc.event_id)
        
        # Comprehensive overlap logic to catch partial and nested intervals [cite: 35, 36]
        if start_time < other.end_time and end_time > other.start_time:
            return True, f"Conflict: Resource is already booked for '{other.title}'." [cite: 34]
            
    return False, ""