from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db, Todo, current_user, login_required
from datetime import datetime

@app.route('/todos')
@login_required
def todos():
    # Get active todos
    active_todos = Todo.query.filter_by(user_id=current_user.id, completed=False).order_by(Todo.due_date).all()
    
    # Get completed todos
    completed_todos = Todo.query.filter_by(user_id=current_user.id, completed=True).order_by(Todo.updated_at.desc()).all()
    
    return render_template('todos.html', 
                          active_todos=active_todos,
                          completed_todos=completed_todos)

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority', 0)
    
    if not title:
        flash('Title is required')
        return redirect(url_for('todos'))
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('todos'))
    
    new_todo = Todo(
        user_id=current_user.id,
        title=title,
        description=description,
        due_date=due_date,
        priority=int(priority)
    )
    
    db.session.add(new_todo)
    db.session.commit()
    
    flash('Todo added successfully')
    return redirect(url_for('todos'))

@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    
    todo.completed = not todo.completed
    todo.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/edit_todo/<int:todo_id>', methods=['POST'])
@login_required
def edit_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority', 0)
    
    if not title:
        flash('Title is required')
        return redirect(url_for('todos'))
    
    todo.title = title
    todo.description = description
    todo.priority = int(priority)
    
    if due_date_str:
        try:
            todo.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('todos'))
    else:
        todo.due_date = None
    
    todo.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Todo updated successfully')
    return redirect(url_for('todos'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(todo)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/get_todo/<int:todo_id>')
@login_required
def get_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    
    todo_data = {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
        'priority': todo.priority,
        'completed': todo.completed
    }
    
    return jsonify(todo_data)
