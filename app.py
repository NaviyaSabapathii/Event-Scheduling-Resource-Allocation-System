from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db, Event, Resource, EventResourceAllocation
from logic import is_resource_conflicting

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'aerele_test_key'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    events = Event.query.order_by(Event.start_time.asc()).all()
    return render_template('index.html', events=events)

@app.route('/resources', methods=['GET', 'POST'])
def resources():
    if request.method == 'POST':
        new_res = Resource(resource_name=request.form['name'], resource_type=request.form['type'])
        db.session.add(new_res)
        db.session.commit()
        flash('Resource added successfully!')
        return redirect(url_for('resources'))
    res_list = Resource.query.all()
    return render_template('resources.html', resources=res_list)

@app.route('/resources/edit/<int:id>', methods=['GET', 'POST'])
def edit_resource(id):
    resource = db.get_or_404(Resource, id)
    if request.method == 'POST':
        resource.resource_name = request.form['name']
        resource.resource_type = request.form['type']
        db.session.commit()
        flash('Resource updated successfully!')
        return redirect(url_for('resources'))
    return render_template('edit_resource.html', resource=resource)

@app.route('/events/add', methods=['GET', 'POST'])
def add_event():
    all_res = Resource.query.all()
    if request.method == 'POST':
        try:
            start = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            end = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            
            if start >= end:
                flash('Error: End time must be after start time.')
                return render_template('events.html', resources=all_res)
            
            selected_ids = request.form.getlist('resources')

            for r_id in selected_ids:
                conflict, msg = is_resource_conflicting(int(r_id), start, end)
                if conflict:
                    flash(msg)
                    return render_template('events.html', resources=all_res)

            new_ev = Event(
                title=request.form['title'], 
                start_time=start, 
                end_time=end, 
                description=request.form.get('description', '')
            )
            db.session.add(new_ev)
            db.session.flush()

            for r_id in selected_ids:
                db.session.add(EventResourceAllocation(event_id=new_ev.event_id, resource_id=int(r_id)))
            
            db.session.commit()
            flash('Event created successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}')
            return render_template('events.html', resources=all_res)
    
    return render_template('events.html', resources=all_res)

@app.route('/events/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    event = db.get_or_404(Event, id)
    all_res = Resource.query.all()
    
    if request.method == 'POST':
        try:
            start = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            end = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            
            if start >= end:
                flash('Error: End time must be after start time.')
                current_ids = [a.resource_id for a in event.allocations]
                return render_template('edit_event.html', event=event, resources=all_res, current_res_ids=current_ids)
            
            selected_ids = request.form.getlist('resources')

            for r_id in selected_ids:
                conflict, msg = is_resource_conflicting(int(r_id), start, end, ignore_event_id=id)
                if conflict:
                    flash(msg)
                    current_ids = [a.resource_id for a in event.allocations]
                    return render_template('edit_event.html', event=event, resources=all_res, current_res_ids=current_ids)

            event.title = request.form['title']
            event.start_time = start
            event.end_time = end
            event.description = request.form.get('description', '')
            
            EventResourceAllocation.query.filter_by(event_id=id).delete()
            
            for r_id in selected_ids:
                db.session.add(EventResourceAllocation(event_id=id, resource_id=int(r_id)))
            
            db.session.commit()
            flash('Event updated successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}')
            current_ids = [a.resource_id for a in event.allocations]
            return render_template('edit_event.html', event=event, resources=all_res, current_res_ids=current_ids)
    
    current_ids = [a.resource_id for a in event.allocations]
    return render_template('edit_event.html', event=event, resources=all_res, current_res_ids=current_ids)

@app.route('/report')
def report():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    results = []
    
    if start_str and end_str:
        try:
            s_dt = datetime.strptime(start_str, '%Y-%m-%d')
            e_dt = datetime.strptime(end_str, '%Y-%m-%d')
            e_dt = e_dt.replace(hour=23, minute=59, second=59)
            
            for r in Resource.query.all():
                total_hrs = 0
                for a in r.allocations:
                    if a.event.start_time >= s_dt and a.event.end_time <= e_dt:
                        duration = (a.event.end_time - a.event.start_time).total_seconds() / 3600
                        total_hrs += duration
                
                upcoming = []
                for a in r.allocations:
                    if a.event.start_time > datetime.now():
                        upcoming.append(f"{a.event.title} ({a.event.start_time.strftime('%b %d, %Y')})")
                
                results.append({
                    'name': r.resource_name,
                    'hours': round(total_hrs, 2),
                    'upcoming': upcoming if upcoming else []
                })
        except Exception as e:
            flash(f'Error generating report: {str(e)}')
    
    return render_template('report.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)