import re
from datetime import datetime
import locale

ROMANIAN_TO_ENGLISH = {
    'ianuarie': 'January', 'februarie': 'February', 'martie': 'March',
    'aprilie': 'April', 'mai': 'May', 'iunie': 'June',
    'iulie': 'July', 'august': 'August', 'septembrie': 'September',
    'octombrie': 'October', 'noiembrie': 'November', 'decembrie': 'December'
}

def extract_date(row):
    # Check if the row is None first and return immediately
    if row is None:
        print("Received a None row to process.")
        return None

    # Now that we know 'row' is not None, we can safely access its keys
    if 'title' not in row or row['title'] is None:
        print("Row has no 'title' key or its value is None.")
        row['date'] = None
        return row

    words = row['title'].split()

    # The date parts are the last three words in the list
    parts = words[-3:]

    if ROMANIAN_TO_ENGLISH.get(parts[1]) is None:
        row['date'] = None
        return row
    english_month = ROMANIAN_TO_ENGLISH[parts[1]]
    english_date_text = f"{parts[0]} {english_month} {parts[2]}"

    # Now, parse the new string using a standard format code
    date_object = datetime.strptime(english_date_text, "%d %B %Y")
    row['date'] = date_object.date().isoformat()

    return row

def get_speaker_and_speech(row):
    pattern = r'(Domnul|Doamna)\s([^:]+?)\s?:\s(.*?)(?=\n(Domnul|Doamna)\s[^:]+?\s?:|\Z)'
    matches = re.findall(pattern, row['conversation'], re.DOTALL)

    speeches = []
    for match in matches:
        full_name = f"{match[0]} {match[1].strip()}"
        speech_content = match[2].strip()
        speeches.append({"speaker": full_name, "speech": speech_content})
    return speeches