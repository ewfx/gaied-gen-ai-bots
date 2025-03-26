from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

def initialize_collections():
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client['email_classification_db']

    # Initialize assigned_to collection
    assigned_to_collection = db['assigned_to']
    assigned_to_collection.insert_many([
        {'name': 'John Doe'},
        {'name': 'Jane Smith'},
        {'name': 'Alice Johnson'},
        {'name': 'Bob Williams'}
    ])

    # Initialize assigned_team collection
    assigned_team_collection = db['assigned_team']
    assigned_team_collection.insert_many([
        {'name': 'Team A'},
        {'name': 'Team B'},
        {'name': 'Team C'},
        {'name': 'Team D'}
    ])

    # Initialize urgency collection
    urgency_collection = db['urgency']
    urgency_collection.insert_many([
        {'level': 'Low'},
        {'level': 'Medium'},
        {'level': 'High'},
        {'level': 'Critical'}
    ])

def insert_request_types():
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client['email_classification_db']
    request_types_collection = db['request_types']

    request_types = [
        ("adjustment", ["reallocation fees", "amendment fees", "reallocation principal"]),
        ("au transfer", ["domestic", "international"]),
        ("closing notice", ["pre-closing", "post-closing"]),
        ("commitment change", ["cashless roll", "decrease", "increase"]),
        ("fee payment", ["ongoing fee", "letter of credit fee"]),
        ("money movement inbound", ["principal", "interest", "principal + interest", "principal + interest + fee"]),
        ("money movement outbound", ["timebound", "foreign currency"]),
        ("document request", ["identity verification", "income statement"]),
        ("account update", ["contact details", "address change"]),
        ("loan extension", ["term extension", "rate modification"]),
        ("collateral review", ["valuation update", "insurance verification"]),
        ("regulatory compliance", ["audit request", "report submission"]),
        ("portfolio rebalancing", ["asset reallocation", "liquidity adjustment"]),
        ("risk assessment", ["credit risk", "market risk"]),
        ("operational review", ["system update", "process improvement"]),
        ("cash management", ["daily reconciliation", "overdraft monitoring"]),
        ("credit line adjustment", ["increase limit", "decrease limit"]),
        ("customer onboarding", ["identity check", "document submission"]),
        ("investment advisory", ["asset allocation", "risk profiling"])
    ]

    documents = [{"request_type": rt, "sub_request_types": srt} for rt, srt in request_types]
    request_types_collection.insert_many(documents)

if __name__ == '__main__':
    # initialize_collections()
    insert_request_types()