import json

import re
from datetime import datetime
from bson.objectid import ObjectId
from db_init import get_db

class EmailClassificationModel:
    def __init__(self, db):
        self.collection = db['email_classifications']
        self.assigned_to_collection = db['assigned_to']
        self.assigned_team_collection = db['assigned_team']
        self.urgency_collection = db['urgency']
        self.request_types_collection = db['request_types']

    def create_email_classification(self, email_classification):
        if not isinstance(email_classification, dict):
            print(f"Error: email_classification is not a dictionary. Type: {type(email_classification)}")
            return None  # Or raise an exception
        email_classification['createdDate'] = datetime.now()
        email_classification['updatedDate'] = datetime.now()
        result = self.collection.insert_one(email_classification)
        return result.inserted_id

    def get_email_classification(self, email_classification_id):
        return self.collection.find_one({"_id": ObjectId(email_classification_id)})

    def update_email_classification(self, email_classification_id, update_data):
        update_data['updatedDate'] = datetime.now()
        self.collection.update_one({"_id": ObjectId(email_classification_id)}, {"$set": update_data})

    def delete_email_classification(self, email_classification_id):
        self.collection.delete_one({"_id": ObjectId(email_classification_id)})

    def find_latest(self):
        """Finds the most recently created email classification."""
        email_classification = self.collection.find_one(sort=[('createdDate', -1)])
        if email_classification:
            email_classification['_id'] = str(email_classification['_id'])  # Convert ObjectId to string for JSON serialization
        return email_classification
    
    def find_all(self):
        """Finds all email classifications."""
        email_classifications = []
        for doc in self.collection.find():
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            email_classifications.append(doc)
        return email_classifications
    
    def fetch_assigned_to(self):
        """Fetches all assigned_to options."""
        return self.assigned_to_collection.find()
    
    def fetch_assigned_team(self):
        """Fetches all assigned_team options."""
        return self.assigned_team_collection.find()
    
    def fetch_urgency(self):
        """Fetches all urgency options."""
        return self.urgency_collection.find()
    
    def get_users_for_team(self, team_name):
        """Fetches all users belonging to the given team from MongoDB."""
        users = [user['user'] for user in self.assigned_to_collection.find({"teams": team_name})]
        return users


    def find_duplicate(self, email_data):
        """
        Checks if the new email_data is a duplicate by comparing its
        extracted email parts (in extracted_texts) with those stored in the DB.
        For each email part in the new data, we search for an existing document
        with an extracted_texts element that has matching 'from', 'subject', and 'body'.

        Returns the duplicate document's ID as a string if found; otherwise, returns None.
        """
        # Iterate over each email part (ignoring attachments)
        for part in email_data:
            if part.get("type", "").lower() != "email":
                continue

            # Normalize the fields (remove any "Re:" prefix, lowercase, and strip whitespace)
            new_from = part.get("from", "").lower().replace("re:", "").strip()
            new_subject = part.get("subject", "").lower().replace("re:", "").strip()
            new_body = part.get("body", "").lower().strip()

            # Use a regex-based query to allow for exact matching (with normalization)
            query = {
                "extracted_texts": {
                    "$elemMatch": {
                        "type": "email",
                        "from": {"$regex": f"^{re.escape(new_from)}$", "$options": "i"},
                        "subject": {"$regex": f"^{re.escape(new_subject)}$", "$options": "i"},
                        "body": {"$regex": f"^{re.escape(new_body)}", "$options": "i"}
                    }
                }
            }

            duplicate = self.collection.find_one(query)
            if duplicate:
                return str(duplicate["_id"])

        return None

    def get_request_type(self, request_type):
        return self.request_types_collection.find_one({"request_type": request_type})
    def get_all_request_types(self):
        return list(self.request_types_collection.find())

    def add_request_type(self, request_type, sub_request_types):
        document = {"request_type": request_type, "sub_request_types": sub_request_types}
        return self.request_types_collection.insert_one(document)

    def update_request_type(self, old_request_type, new_request_type, new_sub_request_types):
        return self.request_types_collection.update_one(
            {"request_type": old_request_type},
            {"$set": {"request_type": new_request_type, "sub_request_types": new_sub_request_types}}
        )

    def delete_request_type(self, request_type):
        return self.request_types_collection.delete_one({"request_type": request_type})

    def add_sub_request_type(self, request_type, sub_request_type):
        return self.request_types_collection.update_one(
            {"request_type": request_type},
            {"$push": {"sub_request_types": sub_request_type}}
        )

    def update_sub_request_type(self, request_type, old_sub, new_sub):
        return self.request_types_collection.update_one(
            {"request_type": request_type, "sub_request_types": old_sub},
            {"$set": {"sub_request_types.$": new_sub}}
        )

    def delete_sub_request_type(self, request_type, sub_request_type):
        return self.request_types_collection.update_one(
            {"request_type": request_type},
            {"$pull": {"sub_request_types": sub_request_type}}
        )

def request_type_json_to_string(json_data):
    result = []
    for item in json_data:
        request_type = item['request_type']
        sub_request_types = item['sub_request_types']
        result.append(f'("{request_type}", {sub_request_types})')
    return "[\n" + ",\n".join(result) + "\n]"


def clean_json_content(file_content):
    """
    Cleans the input string by removing leading/trailing ```json and newlines,
    then attempts to parse it as JSON.

    Args:
        file_content (str): The string content to clean and parse.

    Returns:
        dict: The parsed JSON data as a dictionary, or None if parsing fails.
    """
    # Remove ```json and new lines
    cleaned_content = file_content.replace('```json', '').replace('```', '').replace('\n', '').strip()
    
    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw content: {cleaned_content}")
        return None

# Example usage
if __name__ == "__main__":
    db = get_db()
    email_classification_model = EmailClassificationModel(db)

    print(email_classification_model.fetch_assigned_to().sort('user', 1).distinct('user'))
    # print(request_type_json_to_string(email_classification_model.get_all_request_types()))

    # Read and clean the JSON file
    # file_path = '/Users/bmspr/Documents/GitHub/genai-email-classification/code/src/output/20250324164659_435.json'
    # try:
    #     with open(file_path, 'r') as file:
    #         file_content = file.read()
    #         email_classification = clean_json_content(file_content)
    #         # email_classification = clean_json_content(email_classification)
    # except FileNotFoundError:
    #     print(f"File not found: {file_path}")
    #     exit()
    #
    # if email_classification is None:
    #     print("Failed to parse JSON content. Exiting.")
    #     exit()
    #
    # # Insert email classification
    # email_classification_id = email_classification_model.create_email_classification(email_classification)
    # print(f"Inserted email classification with ID: {email_classification_id}")
    #
    # # Retrieve email classification
    # retrieved_email_classification = email_classification_model.get_email_classification(email_classification_id)
    # print(f"Retrieved email classification: {retrieved_email_classification}")
    #
    # # Update email classification
    # update_data = {"Urgency": "High"}
    # email_classification_model.update_email_classification(email_classification_id, update_data)
    # print(f"Updated email classification with ID: {email_classification_id}")

    # Delete email classification
    # email_classification_model.delete_email_classification(email_classification_id)
    # print(f"Deleted email classification with ID: {email_classification_id}")
