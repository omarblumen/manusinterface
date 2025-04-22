from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db, Conversation, current_user, login_required
from datetime import datetime

@app.route('/conversations')
@login_required
def conversations():
    # Get all conversations for the current user
    user_conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('conversations.html', conversations=user_conversations)

@app.route('/conversation/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    # Get the specific conversation
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
    
    return render_template('conversation_detail.html', conversation=conversation)

@app.route('/add_conversation', methods=['POST'])
@login_required
def add_conversation():
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('Title and content are required')
        return redirect(url_for('conversations'))
    
    new_conversation = Conversation(
        user_id=current_user.id,
        title=title,
        content=content
    )
    
    db.session.add(new_conversation)
    db.session.commit()
    
    flash('Conversation saved successfully')
    return redirect(url_for('conversations'))

@app.route('/edit_conversation/<int:conversation_id>', methods=['POST'])
@login_required
def edit_conversation(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('Title and content are required')
        return redirect(url_for('conversations'))
    
    conversation.title = title
    conversation.content = content
    conversation.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Conversation updated successfully')
    return redirect(url_for('conversations'))

@app.route('/delete_conversation/<int:conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(conversation)
    db.session.commit()
    
    flash('Conversation deleted successfully')
    return redirect(url_for('conversations'))

@app.route('/search_conversations', methods=['GET'])
@login_required
def search_conversations():
    query = request.args.get('query', '')
    
    if not query:
        return redirect(url_for('conversations'))
    
    # Search in title and content
    search_results = Conversation.query.filter_by(user_id=current_user.id).filter(
        (Conversation.title.contains(query)) | (Conversation.content.contains(query))
    ).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('conversations.html', conversations=search_results, search_query=query)
