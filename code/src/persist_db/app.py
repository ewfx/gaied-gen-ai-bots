from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from db_init import get_db
from EmailClassificationDB import EmailClassificationModel, request_type_json_to_string
from extract import extract_email_chain_and_attachments, analyze_with_llm, extract_text_from_pdf_bytes, extract_text_from_docx_bytes, extract_text_from_txt_bytes, extract_email_chain_with_llm  # import the extraction functions
import random

app = Flask(__name__)

# Initialize MongoDB connection and model
db = get_db()
email_classification_model = EmailClassificationModel(db)

@app.route('/')
def index():
    # Fetch all email classifications from MongoDB and render index.html
    all_email_classifications = email_classification_model.find_all()
    return render_template('index.html', all_data=all_email_classifications)

@app.route('/api/email', methods=['GET', 'POST', 'PUT', 'DELETE'])
def email_api():
    if request.method == 'GET':
        # GET a single email classification based on query parameter ?id=<email_id>
        email_id = request.args.get('id')
        if not email_id:
            return jsonify({"error": "Email ID required"}), 400
        email = email_classification_model.get_email_classification(email_id)
        if email:
            email['_id'] = str(email['_id'])
            return jsonify(email)
        else:
            return jsonify({"error": "Email not found"}), 404

    elif request.method == 'POST':
        # POST requires a file attached in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        try:
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension == 'eml':
                eml_bytes = file.read()
                attachment_dir = "./attachments"
                email_chain, full_text = extract_email_chain_and_attachments(eml_bytes, attachment_dir)
            elif file_extension == 'pdf':
                content=file.read()
                full_text = extract_text_from_pdf_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            elif file_extension == 'docx':
                content = file.read()
                full_text = extract_text_from_docx_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            elif file_extension == 'txt':
                content = file.read()
                full_text = extract_text_from_txt_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            # Check for duplicate email chain in the database
            duplicate_id = email_classification_model.find_duplicate(email_chain)

            if duplicate_id:
                # Return a 409 Conflict indicating that the email is a duplicate.
                return jsonify({
                    "message": "Duplicate email found",
                    "duplicate_id": duplicate_id
                }), 409

            request_types = email_classification_model.get_all_request_types()
            request_types = request_type_json_to_string(request_types)
            json_data = analyze_with_llm(email_chain, request_types)
            json_data['extracted_texts'] = email_chain
            json_data['email_file_name'] = file.filename

            json_data['assigned_team'] = json_data['request_type']
            # Fetch all users who belong to the assigned_team
            matching_users = email_classification_model.get_users_for_team(json_data['assigned_team'])
    
            # Assign a random user if there are matching users
            if matching_users:
                json_data['assigned_to'] = random.choice(matching_users)
            else:
                json_data['assigned_to'] = None  # Handle cases where no matching user is found

            new_id = email_classification_model.create_email_classification(json_data)
            return jsonify({"message": "Email created", "id": str(new_id)}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    elif request.method == 'PUT':
        # PUT expects a JSON body with the updated email data including its _id
        data = request.get_json()
        if not data or '_id' not in data:
            return jsonify({"error": "Missing email ID in request body"}), 400
        email_id = data['_id']
        update_data = {k: v for k, v in data.items() if k != '_id'}
        try:
            email_classification_model.update_email_classification(email_id, update_data)
            return jsonify({"message": "Email updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        # DELETE requires an email id in the query parameter ?id=<email_id>
        email_id = request.args.get('id')
        if not email_id:
            return jsonify({"error": "Email ID required"}), 400
        try:
            email_classification_model.delete_email_classification(email_id)
            return jsonify({"message": "Email deleted"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/email/update_existing', methods=['POST'])
def update_existing_email():
    data = request.get_json()
    duplicate_id = data.get('duplicate_id')
    email_chain = data.get('email_chain')
    if not duplicate_id or not email_chain:
        return jsonify({"error": "Missing data"}), 400
    try:
        request_types = email_classification_model.get_all_request_types()
        request_types = request_type_json_to_string(request_types)
        json_data = analyze_with_llm(email_chain, request_types)
        json_data['extracted_texts'] = email_chain
        email_classification_model.update_email_classification(duplicate_id, json_data)
        return jsonify({"message": "Email updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/add_new', methods=['POST'])
def add_new_email():
    data = request.get_json()
    email_chain = data.get('email_chain')
    if not email_chain:
        return jsonify({"error": "Missing email chain"}), 400
    try:
        request_types = email_classification_model.get_all_request_types()
        request_types = request_type_json_to_string(request_types)
        json_data = analyze_with_llm(email_chain, request_types)
        json_data['extracted_texts'] = email_chain
        json_data['assigned_team'] = json_data['request_type']
            # Fetch all users who belong to the assigned_team
        matching_users = email_classification_model.get_users_for_team(json_data['assigned_team'])
    
            # Assign a random user if there are matching users
        if matching_users:
            json_data['assigned_to'] = random.choice(matching_users)
        else:
            json_data['assigned_to'] = None  # Handle cases where no matching user is found
        
        new_id = email_classification_model.create_email_classification(json_data)
        return jsonify({"message": "Email created", "id": str(new_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/discard', methods=['POST'])
def discard_email():
    return jsonify({"message": "Email discarded"}), 200

@app.route('/add', methods=['GET', 'POST'])
def add_email():
    if request.method == 'POST':
        if 'emailFile' not in request.files:
            return "No file provided", 400
        file = request.files['emailFile']
        if file.filename == '':
            return "No file selected", 400
        try:
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension == 'eml':
                eml_bytes = file.read()
                attachment_dir = "./attachments"
                email_chain, full_text = extract_email_chain_and_attachments(eml_bytes, attachment_dir)
            elif file_extension == 'pdf':
                content = file.read()
                full_text = extract_text_from_pdf_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            elif file_extension == 'docx':
                content = file.read()
                full_text = extract_text_from_docx_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            elif file_extension == 'txt':
                content = file.read()
                full_text = extract_text_from_txt_bytes(content)
                email_chain = extract_email_chain_with_llm(full_text)
            else:
                return "Unsupported file type", 400

            # Check for duplicate email chain
            duplicate_id = email_classification_model.find_duplicate(email_chain)
            if duplicate_id:
                duplicate_email = email_classification_model.get_email_classification(duplicate_id)
                return render_template('duplicate.html', new_email=email_chain, old_email=duplicate_email,
                                       duplicate_id=duplicate_id)


            request_types = email_classification_model.get_all_request_types()
            request_types = request_type_json_to_string(request_types)
            json_data = analyze_with_llm(email_chain, request_types)
            json_data['extracted_texts'] = email_chain
            json_data['email_file_name'] = file.filename
            json_data['assigned_team'] = json_data['request_type']
            # Fetch all users who belong to the assigned_team
            matching_users = email_classification_model.get_users_for_team(json_data['assigned_team'])
    
            # Assign a random user if there are matching users
            if matching_users:
                json_data['assigned_to'] = random.choice(matching_users)
            else:
                json_data['assigned_to'] = None  # Handle cases where no matching user is found

            email_classification_id = email_classification_model.create_email_classification(json_data)
            return redirect(url_for('view_email', email_classification_id=email_classification_id))
        except Exception as e:
            return str(e), 500
    return render_template('add.html')


@app.route('/view/<email_classification_id>', methods=['GET'])
def view_email(email_classification_id):
    email_classification = email_classification_model.get_email_classification(email_classification_id)
    if email_classification:
        email_classification['_id'] = str(email_classification['_id'])
        return render_template('view.html', email=email_classification)
    else:
        abort(404)

@app.route('/edit/<email_classification_id>', methods=['GET'])
def edit_email_classification(email_classification_id):
    email_classification = email_classification_model.get_email_classification(email_classification_id)

    if request.method == 'POST':
        assigned_to = request.form.get('assigned_to')
        assigned_team = request.form.get('assigned_team')
        urgency = request.form.get('urgency')
        other_comments = request.form.get('Other_comments')

        update_data = {
            'assigned_to': assigned_to,
            'assigned_team': assigned_team,
            'urgency': urgency,
            'Other comments': other_comments,
        }

        email_classification_model.update_email_classification(email_classification_id, update_data)
        return redirect(url_for('index'))

    else:
        # Fetch the document to edit
        request_type = request.args.get('request_type')
        sub_request_type = request.args.get('sub_request_type')
        from_email = request.args.get('from')

        email_classification = email_classification_model.get_email_classification (email_classification_id)

        if email_classification:
            email_classification['_id'] = str(email_classification['_id'])  # Convert ObjectId to string for JSON serialization

         # Fetch options for assigned_to and assigned_team from the database
        assigned_to_options = email_classification_model.fetch_assigned_to().sort('user', 1).distinct('user')
        assigned_team_options = email_classification_model.fetch_assigned_team().sort('name', 1).distinct('name')
        urgency_options = email_classification_model.fetch_urgency().sort('level', 1).distinct('level')


        return render_template('edit.html', email=email_classification, assigned_to_options=assigned_to_options, assigned_team_options=assigned_team_options, urgency_options=urgency_options)


@app.route('/api/request_types', methods=['GET'])
def api_get_request_types():
    types = email_classification_model.get_all_request_types()
    for rt in types:
        rt['_id'] = str(rt['_id'])
    return jsonify(types)

@app.route('/api/request_types', methods=['POST'])
def api_add_request_type():
    data = request.get_json()
    if not data or 'request_type' not in data or 'sub_request_types' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result = email_classification_model.add_request_type(data['request_type'], data['sub_request_types'])
    return jsonify({"message": "Request type added", "id": str(result.inserted_id)}), 201

@app.route('/api/request_types', methods=['PUT'])
def api_update_request_type():
    data = request.get_json()
    # Expected keys: old_request_type, new_request_type, new_sub_request_types
    if not data or 'old_request_type' not in data or 'new_request_type' not in data or 'new_sub_request_types' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result = email_classification_model.update_request_type(
        data['old_request_type'], data['new_request_type'], data['new_sub_request_types']
    )
    return jsonify({"message": "Request type updated", "matched_count": result.matched_count}), 200

@app.route('/api/request_types', methods=['DELETE'])
def api_delete_request_type():
    data = request.get_json()
    if not data or 'request_type' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result = email_classification_model.delete_request_type(data['request_type'])
    return jsonify({"message": "Request type deleted", "deleted_count": result.deleted_count}), 200

# API endpoints for updating and deleting sub request types
@app.route('/api/request_types/sub', methods=['PUT'])
def api_update_sub_request_type():
    data = request.get_json()
    # Expected keys: request_type, old_sub, new_sub
    if not data or 'request_type' not in data or 'old_sub' not in data or 'new_sub' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result = email_classification_model.update_sub_request_type(
        data['request_type'], data['old_sub'], data['new_sub']
    )
    return jsonify({"message": "Sub request type updated", "matched_count": result.matched_count}), 200

@app.route('/api/request_types/sub', methods=['DELETE'])
def api_delete_sub_request_type():
    data = request.get_json()
    # Expected keys: request_type, sub_request_type
    if not data or 'request_type' not in data or 'sub_request_type' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result = email_classification_model.delete_sub_request_type(
        data['request_type'], data['sub_request_type']
    )
    return jsonify({"message": "Sub request type deleted", "modified_count": result.modified_count}), 200

# UI routes for managing request types
@app.route('/manage_requests', methods=['GET', 'POST'])
def manage_requests():
    if request.method == 'POST':
        request_type = request.form.get('request_type')
        sub_request_types_str = request.form.get('sub_request_types')
        if request_type and sub_request_types_str:
            sub_request_types = [s.strip() for s in sub_request_types_str.split(',') if s.strip()]
            email_classification_model.add_request_type(request_type, sub_request_types)
        return redirect(url_for('manage_requests'))
    request_types = email_classification_model.get_all_request_types()
    return render_template('manage_requests.html', request_types=request_types)

@app.route('/edit_request_type', methods=['GET', 'POST'])
def edit_request_type():
    req_type = request.args.get('request_type')
    if not req_type:
        return redirect(url_for('manage_requests'))
    if request.method == 'POST':
        new_request_type = request.form.get('new_request_type')
        sub_request_types = request.form.getlist('sub_request_types[]')
        email_classification_model.update_request_type(req_type, new_request_type, sub_request_types)
        return redirect(url_for('manage_requests'))
    rt = email_classification_model.get_request_type(req_type)
    return render_template('edit_request_type.html', request_type=rt)

@app.route('/delete_request_type', methods=['GET'])
def delete_request_type_route():
    req_type = request.args.get('request_type')
    if req_type:
        email_classification_model.delete_request_type(req_type)
    return redirect(url_for('manage_requests'))



if __name__ == '__main__':
    app.run(debug=True)

