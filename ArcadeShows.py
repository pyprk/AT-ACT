import requests
import csv
from datetime import datetime

# Airtable settings
airtable_base_id = "appFH3VMECZzDtfnH"  # Your Base ID
airtable_table_id = "tbltgmJmY000JOgRu"  # Your Table ID
airtable_pat = "patSP3cIY9A6rbBQF.c9d7bc5b35ea3e92dabe39f0399cee87a4d174f7266a934569ca5e63fcaae9dc"  # Airtable PAT
airtable_url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_id}"

# WordPress settings
wordpress_url = "https://www.arcadecomedytheater.com"
wordpress_user = "rkemick"
wordpress_app_password = "Kqsr hAp7 8Hmq DDQ3 GaKg ak16"  # Application password
wordpress_event_endpoint = f"{wordpress_url}/wp-json/tribe/events/v1/events"

# Fetch events from Airtable with filtering
def fetch_airtable_events():
    headers = {"Authorization": f"Bearer {airtable_pat}"}
    params = {
        "filterByFormula": "AND(NOT({Added to Wordpress}), IS_AFTER({Date for Calendar}, TODAY()), LEN({Day of the Week}) > 0)"
    }
    print(f"Requesting Airtable API with URL: {airtable_url}")
    print(f"Params: {params}")
    response = requests.get(airtable_url, headers=headers, params=params)
    print(f"Response Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Response Content: {response.text}")
    response.raise_for_status()
    records = response.json()["records"]
    print(f"Number of events fetched: {len(records)}")
    return records

# Upload events to WordPress as pending
def upload_event_to_wordpress(event_data):
    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(wordpress_user, wordpress_app_password)}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": event_data["fields"].get("Show Name", "Untitled Event"),
        "content": event_data["fields"].get("Long Promo Blurb", ""),
        "status": "pending",  # Set event as pending
        "start_date": event_data["fields"].get("Date for Calendar", ""),
        "end_date": event_data["fields"].get("Date for Calendar", ""),  # Use same date unless you have separate end date
        "start_time": event_data["fields"].get("Showtime", "00:00:00"),  # Default to midnight if missing
        "categories": [event_data["fields"].get("Show Category", "uncategorized")],  # Replace with actual category slug or ID
        "cost": event_data["fields"].get("Ticket Price", ""),
        "url": event_data["fields"].get("Showclix Ticket Link", ""),  # Event website link
    }

    # Handle optional excerpt field
    if "Show Promo Blurb" in event_data["fields"]:
        payload["excerpt"] = event_data["fields"]["Show Promo Blurb"]

    print(f"Uploading event to WordPress with payload: {payload}")
    response = requests.post(wordpress_event_endpoint, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Event uploaded successfully: {response.json()}")
    else:
        print(f"Failed to upload event: {response.status_code} - {response.text}")

# Mark events as exported in Airtable
def mark_as_exported(events):
    headers = {
        "Authorization": f"Bearer {airtable_pat}",
        "Content-Type": "application/json"
    }
    for event in events:
        record_id = event["id"]
        data = {"fields": {"Added to Wordpress": True}}
        print(f"Updating record ID: {record_id} with payload: {data}")
        response = requests.patch(f"{airtable_url}/{record_id}", json=data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to update record: {response.status_code} - {response.text}")

# Main function
def automate_event_upload():
    try:
        events = fetch_airtable_events()
        if not events:
            print("No events to export.")
            return

        for event in events:
            upload_event_to_wordpress(event)
            mark_as_exported([event])  # Mark only the processed event

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the script
if __name__ == "__main__":
    automate_event_upload()
