from dotenv import load_dotenv
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, template_folder="extension")
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
    minutes, seconds = currentTimeStamp.split(':')
    currentTimeStampInSeconds = int(minutes) * 60 + int(seconds)
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

            
            page_id = get_page_id(videoTitle)
            if page_id is not None:

                append_block_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
                append_payload = {
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": noteTitle}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": currentTimeStamp, "link": {"url": videoUrlWithTimeStamp}}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": notesText}}
                                ]
                            },
                        }
                    ]
                }

                res = requests.patch(append_block_url, headers=headers, json=append_payload)
            else:
                print("Creating a new page")

                create_page_url = "https://api.notion.com/v1/pages"
                payload = {
                    "parent": {"database_id": notes_database_id},
                    "properties": {
                        "Title": {"title": [{"text": {"content": videoTitle}}]},
                        "URL": {"rich_text": [{"text": {"content": videoUrl}}]},
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": noteTitle}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": currentTimeStamp, "link": {"url": videoUrlWithTimeStamp}}},
                                    {"type": "text", "text": {"content": "\n"}},
                                    {"type": "text", "text": {"content": notesText}}
                                ]
                            },
                        }
                    ]
                }

                res = requests.post(create_page_url, headers=headers, json=payload)

            print("Notion API Response Status Code:", res.status_code)

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
