# 📄 High-Level Design Document

## 📌 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Data Flow](#data-flow)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [UI Design](#ui-design)
- [Technologies Used](#technologies-used)

---

## 🎯 Overview
This project is an email classification system that processes emails, extracts relevant information, and classifies them into predefined categories. It includes functionalities for managing request types and sub-request types, viewing and editing email classifications, and handling attachments.

## 🏛️ Architecture
The system follows a client-server architecture with the following components:
- **Frontend**: HTML templates and JavaScript for the user interface.
- **Backend**: Flask application providing RESTful API endpoints.
- **Database**: MongoDB for storing email classifications and request types.

## 🧩 Components
### 1. **Flask Application (`app.py`)**
   - Manages API endpoints for email classifications and request types.
   - Renders HTML templates for the user interface.

### 2. **Email Processing (`extract.py`)**
   - Extracts email content and attachments.
   - Analyzes email content using a language model.

### 3. **Database Model (`EmailClassificationDB.py`)**
   - Interacts with MongoDB for CRUD operations on email classifications and request types.

### 4. **Email Generation (`emailgen.py`)**
   - Generates test emails with attachments for testing the system.

### 5. **Database Initialization (`dropdownvalues.py`)**
   - Initializes MongoDB collections with predefined values.

## 🔄 Data Flow
1. **Email Upload**: User uploads an email file.
2. **Email Processing**: The system extracts content and attachments, analyzes the content, and classifies the email.
3. **Database Storage**: The classified email is stored in MongoDB.
4. **UI Interaction**: Users can view, edit, and manage email classifications and request types through the web interface.

## 🌐 API Endpoints
### Email Classification Endpoints
- `GET /api/email`: Retrieve a single email classification.
- `POST /api/email`: Upload and classify a new email.
- `PUT /api/email`: Update an existing email classification.
- `DELETE /api/email`: Delete an email classification.

### Request Types Endpoints
- `GET /api/request_types`: Retrieve all request types.
- `POST /api/request_types`: Add a new request type.
- `PUT /api/request_types`: Update an existing request type.
- `DELETE /api/request_types`: Delete a request type.
- `PUT /api/request_types/sub`: Update a sub-request type.
- `DELETE /api/request_types/sub`: Delete a sub-request type.

## 🗃️ Database Schema
### Collections
- **email_classifications**
  - Fields: `_id`, `request_type`, `sub_request_type`, `from`, `to`, `subject`, `customer_name`, `last_date`, `urgency`, `shortened_description`, `confidence_score`, `reason`, `secondary_intent`, `createdDate`, `updatedDate`, `extracted_texts`, `email_file_name`, `assigned_team`, `assigned_to`
- **request_types**
  - Fields: `_id`, `request_type`, `sub_request_types`
- **assigned_to**
  - Fields: `_id`, `name`
- **assigned_team**
  - Fields: `_id`, `name`
- **urgency**
  - Fields: `_id`, `level`

## 🎨 UI Design
### HTML Templates
- **index.html**: Displays all email classifications.
- **add.html**: Form to upload a new email.
- **view.html**: View details of a single email classification.
- **edit.html**: Edit an existing email classification.
- **manage_requests.html**: Manage request types and sub-request types.
- **edit_request_type.html**: Edit a request type.

### JavaScript
- Handles UI interactions and API calls for managing email classifications and request types.

## 🛠️ Technologies Used
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Backend**: Python, Flask
- **Database**: MongoDB
- **Libraries**: pymongo, python-docx, reportlab, pillow, pytesseract, beautifulsoup4, google-genai, python-dotenv, PyMuPDF