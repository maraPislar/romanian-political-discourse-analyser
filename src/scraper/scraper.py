from bs4 import BeautifulSoup

import subprocess
import os
import sqlite3
from process_data import extract_date, get_speaker_and_speech


def extract_meeting_data(soup):
    data = {
        'title': None,
        'intro': None,
        'conversation': ""
    }

    # extract title
    title_h3 = soup.select_one('div.content-right div.box-title.clearfix h3')
    if title_h3:
        data['title'] = title_h3.get_text(strip=True)

    old_div = soup.find('div', id='olddiv')
    if not old_div:
        return data
        
    transcript_table_body = old_div.select_one('table > tbody')
    if not transcript_table_body:
        transcript_table_body = old_div.find('table')
        if not transcript_table_body:
            print("Error: Could not find the main transcript table or its tbody.")
            return data

    rows = transcript_table_body.find_all('tr', valign='top', recursive=False)
    if not rows:
        return data

    # extract intro
    intro_texts_collected = []
    intro_section_identified = False
    if rows:
        intro_row_td = rows[0].find('td', {'width': '100%'})
        if intro_row_td:
            intro_paragraphs = intro_row_td.find_all('p', align='justify')
            
            temp_intro_check_text = ' '.join([p.get_text(strip=True) for p in intro_paragraphs])
            if "Şedinţa a început" in temp_intro_check_text or "Lucrările şedinţei au fost conduse" in temp_intro_check_text:
                intro_section_identified = True
            
            if intro_section_identified:
                for p in intro_paragraphs:
                    intro_texts_collected.append(p.get_text(separator=' ', strip=True))
                if intro_texts_collected:
                    data['intro'] = ' '.join(intro_texts_collected)

    # extract conversation
    all_turn_text_blocks = []
    conversation_rows_start_index = 0
    if data['intro'] and intro_section_identified: 
        conversation_rows_start_index = 1

    for i in range(conversation_rows_start_index, len(rows)):
        row = rows[i]
        # print(row)
        # break
        content_td = row.find('td', {'width': '100%'})
        if not content_td:
            continue

        # Get text from all <p align="justify"> tags within this specific 'td'
        # This will include speaker names and their dialogue as it appears in the HTML paragraphs
        paragraphs_in_td = content_td.find_all('p', align='justify')

        if paragraphs_in_td:
            text = paragraphs_in_td[0].get_text(separator=' ', strip=True)
            if text:
                all_turn_text_blocks.append(text)

    if all_turn_text_blocks:
        # Join the text blocks from each turn/TD with a double newline for separation
        data['conversation'] = "\n\n".join(all_turn_text_blocks)
    
    return data

def scrape_website(base_url, start_id, end_id, output_path):
    # Iterate through the range of IDs
    for current_id in range(start_id, end_id + 1):
        # Construct the full URL for the current ID
        url = base_url.format(current_id)

        # Construct the output filename based on the current ID
        filename = output_path.format(current_id)

        # Build the curl command as a list
        command = [
            "curl",
            "-o",
            filename,
            url
        ]

        print(f"Executing command: {' '.join(command)}")

        # Execute the command and handle potential errors
        try:
            subprocess.run(command, check=True)
            print(f"Successfully saved content to {filename}")
        except FileNotFoundError:
            print("Error: The 'curl' command was not found. Please ensure it's installed and in your system's PATH.")
            break  # Exit the loop if curl isn't found
        except subprocess.CalledProcessError as e:
            print(f"Error executing curl for URL {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def get_meeting_data(filename):
    # beautiful soup stuf
    try:
        with open(filename, 'r', encoding='iso-8859-2') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}")
        print(f"There was an issue decoding the file. Ensure it is saved with 'iso-8859-2' encoding or try other common encodings if 'iso-8859-2' also fails (e.g., 'latin1', 'windows-1250').")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    data = extract_meeting_data(soup)

    if data['conversation'] and data['title'] and data['intro']:
        return data
    else:
        return None

if __name__ == "__main__":

    # Define the base URL with a placeholder for the ID
    base_url = "https://www.cdep.ro/pls/steno/steno2015.stenograma?ids={}&idl=1"
    # Define the base path for the output files
    output_path = "data/htmls/{}.html"

    # Define the range of IDs to scrape. For example, from 8900 to 8999
    start_id = 8900
    end_id = 8928

    # Ensure the parent directory exists before starting the loop
    os.makedirs("data/htmls/", exist_ok=True)

    # scrape_website(base_url, start_id, end_id, output_path)

    # Connect to database
    conn = sqlite3.connect('data/db.sqlite')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS speeches (
            id INTEGER PRIMARY KEY,
            meeting_id INTEGER,
            title TEXT,
            intro TEXT,
            date TEXT,
            speaker TEXT,
            content TEXT
        )
    ''')

    for current_id in range(start_id, end_id + 1):
        filename = output_path.format(current_id)
        data = get_meeting_data(filename)
        if data is None:
            continue

        data = extract_date(data)
        conversations = get_speaker_and_speech(data)

        for conversation in conversations:
            cur.execute("INSERT INTO speeches (meeting_id, title, intro,date, speaker, content) VALUES (?, ?, ?, ?, ?, ?)",
                (current_id, data['title'], data['intro'], data['date'], conversation['speaker'], conversation['speech']))
    
    conn.commit()
    conn.close()
        