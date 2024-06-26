from dotenv import load_dotenv
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

app = Flask(__name__, template_folder="extension")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pagedetail.db"
db.init_app(app)

class PageDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String, unique=True, nullable=False)
    videoTitle = db.Column(db.String, unique=True, nullable=False)

with app.app_context():
    db.create_all()


CORS(app)

load_dotenv()

notion_api_token = os.getenv("NOTION_API_TOKEN")
notes_database_id = os.getenv("NOTES_DB_ID")

headers = {
    "Authorization": f"Bearer {notion_api_token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def get_url_with_timestamp(videoUrl, currentTimeStamp):
    time_parts = currentTimeStamp.split(':')

    if len(time_parts) == 2:  # Format: MM:SS
        minutes, seconds = time_parts
        currentTimeStampInSeconds = int(minutes) * 60 + int(seconds)
    elif len(time_parts) == 3:  # Format: HH:MM:SS
        hours, minutes, seconds = time_parts
        currentTimeStampInSeconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    else:
        raise ValueError("Invalid time format. Use either MM:SS or HH:MM:SS")

    videoUrlWithTimeStamp = f'{videoUrl}#t={currentTimeStampInSeconds}'
    return videoUrlWithTimeStamp

def get_page_id(videoTitle):
    notion_query_url = f"https://api.notion.com/v1/databases/{notes_database_id}/query"
    query_payload = {
        "filter": {
            "property": "Title",
            "title": {
                "equals": videoTitle
            }
        }
    }

    res = requests.post(notion_query_url, headers=headers, json=query_payload)
    print("Fetching Page ID")
    if res.status_code == 200:
        response_data = res.json()
        results = response_data.get("results", [])
        if results:
            return results[0]["id"]
        else:
            return None  
    else:
        raise Exception(f"Error getting page ID: {res.text}")

@app.route("/add_notes", methods=["POST"])
def add_notes():
    if request.method == "POST":
        try:
            data = request.json  

            videoUrl = data["videoUrl"]
            videoTitle = data["videoTitle"]
            currentTimeStamp = data["currentTimeStamp"]
            videoUrlWithTimeStamp = get_url_with_timestamp(videoUrl, currentTimeStamp)
            noteTitle = data["noteTitle"]
            notesText = data["largeText"]

            existing_entry = PageDetail.query.filter_by(videoTitle=videoTitle).first()
            

            if existing_entry:
                page_id = existing_entry.page_id
                append_block_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
                append_payload = {
                     "children": [
                                    {
                                    "object": "block",
                                    "type": "heading_3",
                                    "heading_3": {
                                        "rich_text": [{ "type": "text", "text": { "content": noteTitle } }],
                                    "children": [
                                                {
                                                    "object": "block",
                                                    "type": "paragraph",
                                                    "paragraph": {
                                                        "rich_text": [
                                                            {"type": "text", "text": { "content": currentTimeStamp, "link": { "url": videoUrlWithTimeStamp }}},
                                                            {"type": "text", "text": {"content": "\n"}},
                                                            {"type": "text", "text": {"content": notesText}}
                                                        ],
                                                    },
                                                }
                                            ],
                                    "color":"pink_background",
                                }}]}

                res = requests.patch(append_block_url, headers=headers, json=append_payload)
            else:
                print("Creating a new page")

                create_page_url = "https://api.notion.com/v1/pages"
                payload = {
                    "parent": {"database_id": notes_database_id},
                    "properties": {
                        "Title": {"title": [{"text": {"content": videoTitle}}]},
                        "URL": {"url":  videoUrl},
                    },
                    "children": [
                                    {
                                    "object": "block",
                                    "type": "heading_3",
                                    "heading_3": {
                                        "rich_text": [{ "type": "text", "text": { "content": noteTitle } }],
                                    "children": [
                                                {
                                                    "object": "block",
                                                    "type": "paragraph",
                                                    "paragraph": {
                                                        "rich_text": [
                                                            {"type": "text", "text": { "content": currentTimeStamp, "link": { "url": videoUrlWithTimeStamp }}},
                                                            {"type": "text", "text": {"content": "\n"}},
                                                            {"type": "text", "text": {"content": notesText}}
                                                        ],
                                                    },
                                                }
                                            ],
                                    "color":"pink_background",
                                }}]
                }
                res = requests.post(create_page_url, headers=headers, json=payload)

                page_id = get_page_id(videoTitle)
                new_entry = PageDetail(page_id=page_id, videoTitle=videoTitle)
                db.session.add(new_entry)
                db.session.commit()

            print("Notion API Response Status Code:", res.status_code)
            print(res)

            if res.status_code == 200:
                return jsonify({"success": True, "message": "Note added successfully"}), 200
            else:
                return jsonify({"success": False, "message": f"Error: {res.text}"}), res.status_code

        except Exception as e:
            print("Error processing data:", str(e))
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        return jsonify({"success": False, "error": "Method not allowed"}), 405


if __name__ == '__main__':
    app.run(debug=True)
