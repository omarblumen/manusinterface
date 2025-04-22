from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import json
from icalendar import Calendar, Event as ICalEvent
import pytz
from app import app, db, CalendarEvent, Reminder, current_user, login_required

# Calendar routes
@app.route('/calendar')
@login_required
def calendar():
    # Get upcoming events
    events = CalendarEvent.query.filter_by(user_id=current_user.id).filter(CalendarEvent.start_time >= datetime.utcnow()).order_by(CalendarEvent.start_time).all()
    
    return render_template('calendar.html', events=events)

@app.route('/get_calendar_events')
@login_required
def get_calendar_events():
    # Get all events for the calendar view
    events = CalendarEvent.query.filter_by(user_id=current_user.id).all()
    
    # Format for FullCalendar
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'description': event.description,
            'location': event.location
        })
    
    return jsonify(calendar_events)

@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    title = request.form.get('title')
    description = request.form.get('description')
    location = request.form.get('location')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if not title or not start_time_str or not end_time_str:
        flash('Title, start time, and end time are required')
        return redirect(url_for('calendar'))
    
    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format')
        return redirect(url_for('calendar'))
    
    if end_time <= start_time:
        flash('End time must be after start time')
        return redirect(url_for('calendar'))
    
    new_event = CalendarEvent(
        user_id=current_user.id,
        title=title,
        description=description,
        location=location,
        start_time=start_time,
        end_time=end_time
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    flash('Event added successfully')
    return redirect(url_for('calendar'))

@app.route('/get_event/<int:event_id>')
@login_required
def get_event(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    
    return jsonify({
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'location': event.location,
        'start_time': event.start_time.isoformat(),
        'end_time': event.end_time.isoformat()
    })

@app.route('/edit_event/<int:event_id>', methods=['POST'])
@login_required
def edit_event(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    description = request.form.get('description')
    location = request.form.get('location')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if not title or not start_time_str or not end_time_str:
        flash('Title, start time, and end time are required')
        return redirect(url_for('calendar'))
    
    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format')
        return redirect(url_for('calendar'))
    
    if end_time <= start_time:
        flash('End time must be after start time')
        return redirect(url_for('calendar'))
    
    event.title = title
    event.description = description
    event.location = location
    event.start_time = start_time
    event.end_time = end_time
    
    db.session.commit()
    
    flash('Event updated successfully')
    return redirect(url_for('calendar'))

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/export_calendar')
@login_required
def export_calendar():
    format_type = request.args.get('format', 'ics')
    date_range = request.args.get('range', 'all')
    
    # Build query based on parameters
    query = CalendarEvent.query.filter_by(user_id=current_user.id)
    
    if date_range == 'upcoming':
        query = query.filter(CalendarEvent.start_time >= datetime.utcnow())
    elif date_range == 'custom':
        start_date_str = request.args.get('start')
        end_date_str = request.args.get('end')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
                query = query.filter(CalendarEvent.start_time >= start_date, CalendarEvent.start_time < end_date)
            except ValueError:
                flash('Invalid date format')
                return redirect(url_for('calendar'))
    
    events = query.all()
    
    if format_type == 'ics':
        # Export as iCalendar
        cal = Calendar()
        cal.add('prodid', '-//Assistant App//EN')
        cal.add('version', '2.0')
        
        for event in events:
            ical_event = ICalEvent()
            ical_event.add('summary', event.title)
            ical_event.add('description', event.description or '')
            ical_event.add('location', event.location or '')
            ical_event.add('dtstart', event.start_time.replace(tzinfo=pytz.UTC))
            ical_event.add('dtend', event.end_time.replace(tzinfo=pytz.UTC))
            ical_event.add('dtstamp', datetime.utcnow().replace(tzinfo=pytz.UTC))
            ical_event['uid'] = f'{event.id}@assistantapp.example.com'
            
            cal.add_component(ical_event)
        
        return cal.to_ical(), 200, {
            'Content-Type': 'text/calendar',
            'Content-Disposition': 'attachment; filename=calendar.ics'
        }
    
    elif format_type == 'json':
        # Export as JSON
        events_data = []
        
        for event in events:
            event_data = {
                'title': event.title,
                'description': event.description,
                'location': event.location,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat()
            }
            events_data.append(event_data)
        
        return jsonify(events_data)
    
    else:
        flash('Invalid export format')
        return redirect(url_for('calendar'))

@app.route('/sync_calendar', methods=['POST'])
@login_required
def sync_calendar():
    # En una implementación real, esto usaría la API de Calendario de Apple o Google Calendar API
    # Para demostración, simulamos una sincronización exitosa
    
    try:
        # Simular retraso de llamada a API
        # time.sleep(1)
        
        # Devolver respuesta de éxito
        return jsonify({
            'success': True,
            'message': 'Calendar synced successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Rutas de recordatorios
@app.route('/reminders')
@login_required
def reminders():
    # Obtener recordatorios activos
    active_reminders = Reminder.query.filter_by(user_id=current_user.id, completed=False).order_by(Reminder.reminder_time).all()
    
    # Obtener recordatorios completados
    completed_reminders = Reminder.query.filter_by(user_id=current_user.id, completed=True).order_by(Reminder.reminder_time.desc()).all()
    
    return render_template('reminders.html', 
                          active_reminders=active_reminders,
                          completed_reminders=completed_reminders)

@app.route('/add_reminder', methods=['POST'])
@login_required
def add_reminder():
    title = request.form.get('title')
    description = request.form.get('description')
    reminder_time_str = request.form.get('reminder_time')
    
    if not title or not reminder_time_str:
        flash('Title and reminder time are required')
        return redirect(url_for('reminders'))
    
    try:
        reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format')
        return redirect(url_for('reminders'))
    
    new_reminder = Reminder(
        user_id=current_user.id,
        title=title,
        description=description,
        reminder_time=reminder_time
    )
    
    db.session.add(new_reminder)
    db.session.commit()
    
    flash('Reminder added successfully')
    return redirect(url_for('reminders'))

@app.route('/get_reminder/<int:reminder_id>')
@login_required
def get_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    
    return jsonify({
        'id': reminder.id,
        'title': reminder.title,
        'description': reminder.description,
        'reminder_time': reminder.reminder_time.isoformat(),
        'completed': reminder.completed
    })

@app.route('/edit_reminder/<int:reminder_id>', methods=['POST'])
@login_required
def edit_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    description = request.form.get('description')
    reminder_time_str = request.form.get('reminder_time')
    
    if not title or not reminder_time_str:
        flash('Title and reminder time are required')
        return redirect(url_for('reminders'))
    
    try:
        reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format')
        return redirect(url_for('reminders'))
    
    reminder.title = title
    reminder.description = description
    reminder.reminder_time = reminder_time
    
    db.session.commit()
    
    flash('Reminder updated successfully')
    return redirect(url_for('reminders'))

@app.route('/toggle_reminder/<int:reminder_id>', methods=['POST'])
@login_required
def toggle_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    reminder.completed = data.get('completed', not reminder.completed)
    reminder.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_reminder/<int:reminder_id>', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/sync_reminders', methods=['POST'])
@login_required
def sync_reminders():
    # En una implementación real, esto usaría la API de Recordatorios de Apple
    # Para demostración, simulamos una sincronización exitosa
    
    try:
        # Simular retraso de llamada a API
        # time.sleep(1)
        
        # Devolver respuesta de éxito
        return jsonify({
            'success': True,
            'message': 'Reminders synced successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
