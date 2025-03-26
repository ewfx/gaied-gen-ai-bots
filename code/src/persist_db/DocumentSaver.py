import os
from EmailClassificationDB import EmailClassificationModel, clean_json_content
from db_init import get_db

class DocumentSaver:
    def __init__(self):
        self.db = get_db()
        self.email_classification_model = EmailClassificationModel(self.db)

    def save_document(self, file_path):
        try:
            # Read and clean the JSON file
            with open(file_path, 'r') as file:
                file_content = file.read()
                email_classification = clean_json_content(file_content)
                email_classification = clean_json_content(email_classification)

            if email_classification is None:
                print(f"Error: Failed to parse JSON from file: {file_path}")
                return  # Or raise an exception

            # Check for duplicates
            existing_document = self.email_classification_model.collection.find_one({
                'request_type': email_classification['request_type'],
                'sub_request_type': email_classification['sub_request_type'],
                'from': email_classification['from']
            })

            if existing_document:
                print(f"Duplicate found: {existing_document['_id']}")
                # Optionally update the existing document
                self.email_classification_model.update_email_classification(existing_document['_id'], email_classification)
                print(f"Updated existing email classification with ID: {existing_document['_id']}")
            else:
                # Insert new email classification
                email_classification_id = self.email_classification_model.create_email_classification(email_classification)
                if email_classification_id is None:
                    print(f"Error: Failed to save email classification to database for file: {file_path}")
                    return
                print(f"Inserted email classification with ID: {email_classification_id}")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return

# Example usage
if __name__ == "__main__":
    document_saver = DocumentSaver()
    file_path = 'D:\\Workspace\\VSCode-workspace\\Python\\GenAI-EmailClassification\\genai-email-classification\\code\\src\\output\\20250324164705_571.json'
    document_saver.save_document(file_path)
