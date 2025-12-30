import csv
import asyncio
import os
import re
import argparse
import sys
from telethon import TelegramClient, functions, errors
from telethon.tl.types import MessageMediaPoll

# --- CONFIGURATION ---
api_id = 'YOUR_API_ID'       
api_hash = 'YOUR_API_HASH'   
channel_username = 'https://t.me/+WEHp0n5fJCw5MWM1' # Active Medcall
# ---------------------

def get_text(text_obj):
    if hasattr(text_obj, 'text'):
        return text_obj.text
    return str(text_obj) if text_obj else ""

def load_existing_data(filename):
    """Loads current CSV into a dictionary keyed by Message ID."""
    database = {}
    
    if not filename:
        return database
    
    if not os.path.exists(filename):
        print(f"Note: The input file '{filename}' was not found.")
        return database
    
    print(f"Loading existing data from {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    msg_id = int(row['ID'])
                    database[msg_id] = row
                except ValueError:
                    continue
    except Exception as e:
        print(f"Warning: Could not read existing file: {e}")
    
    print(f"Loaded {len(database)} existing questions.")
    return database

def save_to_csv(data, filename):
    if not data: return
    # Added 'Question Number' to headers
    headers = ['ID', 'Question Number', 'Date', 'Topic', 'Tags', 'Question', 'Correct Answer', 'Explanation', 
               'Option 1', 'Option 2', 'Option 3', 'Option 4']
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        dict_writer.writeheader()
        dict_writer.writerows(data)

async def main(input_csv, output_csv):
    async with TelegramClient('anon', api_id, api_hash) as client:
        print(f"--- Connecting to {channel_username} ---")
        channel_entity = await client.get_entity(channel_username)

        # 1. Load Data
        known_questions = load_existing_data(input_csv)
        
        # --- SAFETY CHECK ---
        if not known_questions:
            print("\n" + "!"*60)
            print("WARNING: No existing data loaded. You are about to start a FRESH SCRAPE.")
            if input_csv:
                print(f"Reason: Input file '{input_csv}' was not found or is empty.")
            else:
                print("Reason: No input file was specified (-i).")
            print("This process will scan the ENTIRE channel history.")
            print("!"*60 + "\n")
            
            confirm = input("Are you sure you want to proceed? (y/n): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Aborting operation.")
                return
            print("\nProceeding with Fresh Scrape...\n")
        # --------------------

        print(f"Output will be saved to: {output_csv}")
        print("-" * 60)

        processed_rows = []
        last_context_text = ""
        
        async for message in client.iter_messages(channel_entity, reverse=True, limit=None):
            
            # A. CAPTURE CONTEXT
            if message.text and not message.media:
                last_context_text = message.text
                continue 

            # B. PROCESS POLLS
            if message.media and isinstance(message.media, MessageMediaPoll):
                poll = message.media.poll
                
                if not poll.quiz:
                    last_context_text = ""
                    continue

                # --- 1. EXTRACT TAGS, TOPIC, AND QUESTION NUMBER ---
                tags = []
                topic = ""
                question_number = "" # <--- NEW
                
                if last_context_text:
                    # 1. Extract Tags
                    tags = re.findall(r'(#\w+)', last_context_text)
                    
                    # 2. Extract Topic
                    topic_match = re.search(r'Topic:\s*(.+)', last_context_text, re.IGNORECASE)
                    if topic_match:
                        topic = topic_match.group(1).strip()
                        
                    # 3. Extract Question Number (e.g. "Quiz 1367")
                    # Looks for "Quiz" followed by spaces and then digits
                    q_num_match = re.search(r'Quiz\s*(\d+)', last_context_text, re.IGNORECASE)
                    if q_num_match:
                        question_number = q_num_match.group(1)
                        
                last_context_text = ""
                
                # --- PREPARE VISUALS ---
                status_label = ""
                question_text = get_text(poll.question)
                ans_text = "N/A"
                expl_text = ""
                
                # --- 2. CHECK EXISTING ---
                if message.id in known_questions:
                    # === FAST PATH (Update Old) ===
                    row = known_questions[message.id]
                    
                    # Update metadata (including Question Number)
                    row['Topic'] = topic
                    row['Tags'] = ", ".join(tags)
                    row['Question Number'] = question_number # <--- NEW
                    
                    if 'Explanation' not in row: row['Explanation'] = ""
                    
                    # For display purposes only
                    ans_text = row.get('Correct Answer', 'N/A')
                    expl_text = row.get('Explanation', '')
                    status_label = "MERGE/UPDATE"
                    
                    processed_rows.append(row)
                    
                else:
                    # === SLOW PATH (Scrape New) ===
                    status_label = "NEW SCRAPE"
                    
                    options_text = []
                    option_bytes_map = {} 
                    for answer in poll.answers:
                        txt = get_text(answer.text)
                        options_text.append(txt)
                        option_bytes_map[answer.option] = txt

                    def parse_results(results_obj):
                        ans = "N/A"
                        expl = ""
                        found = False
                        if results_obj and results_obj.results:
                            for result in results_obj.results:
                                if hasattr(result, 'correct') and result.correct:
                                    ans = option_bytes_map.get(result.option, "Unknown")
                                    found = True
                                    break
                            if hasattr(results_obj, 'solution') and results_obj.solution:
                                expl = get_text(results_obj.solution)
                        return ans, expl, found

                    ans_text, expl_text, found = parse_results(message.media.results)

                    if not found:
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                print(f"   [ID:{message.id}] Answer hidden... Voting to reveal.")
                                await client(functions.messages.SendVoteRequest(
                                    peer=channel_entity,
                                    msg_id=message.id,
                                    options=[poll.answers[0].option]
                                ))
                                await asyncio.sleep(3.0) 
                                updated_msg = await client.get_messages(channel_entity, ids=message.id)
                                ans_text, expl_text, found = parse_results(updated_msg.media.results)
                                break
                            except errors.FloodWaitError as e:
                                print(f"   [!] FloodWait: Sleeping {e.seconds + 5}s...")
                                await asyncio.sleep(e.seconds + 5)
                            except Exception as e:
                                print(f"   [!] Error: {e}")
                                break

                    row = {
                        'ID': message.id,
                        'Question Number': question_number, # <--- NEW
                        'Date': message.date,
                        'Topic': topic,
                        'Tags': ", ".join(tags),
                        'Question': question_text,
                        'Correct Answer': ans_text,
                        'Explanation': expl_text,
                        'Option 1': options_text[0] if len(options_text) > 0 else "",
                        'Option 2': options_text[1] if len(options_text) > 1 else "",
                        'Option 3': options_text[2] if len(options_text) > 2 else "",
                        'Option 4': options_text[3] if len(options_text) > 3 else "",
                    }
                    processed_rows.append(row)

                # --- 3. VERBOSE OUTPUT ---
                clean_q = question_text.replace('\n', ' ')
                clean_a = ans_text.replace('\n', ' ')
                clean_e = expl_text.replace('\n', ' ')[:60] 
                
                # Update print to show Quiz #
                q_num_display = f"#{question_number}" if question_number else "No #"
                print(f"[{status_label}] Quiz {q_num_display} | ID: {message.id}")
                print(f"    Topic: {topic}")
                print(f"    Q: {clean_q[:60]}...")
                print(f"    A: {clean_a}")
                if clean_e:
                    print(f"    E: {clean_e}...")
                print("-" * 60)
                # ------------------------------------

                # --- 4. BATCH SAVE ---
                if len(processed_rows) % 20 == 0:
                    save_to_csv(processed_rows, output_csv)
                    print(f"   >>> Auto-saved batch of {len(processed_rows)} questions <<<")

        # Final Save
        save_to_csv(processed_rows, output_csv)
        print(f"\nCOMPLETED! Total {len(processed_rows)} questions saved to {output_csv}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Telegram Quiz Scraper & Merger")
    parser.add_argument('-i', '--input', required=False, help="Input CSV filename to merge.")
    parser.add_argument('-o', '--output', required=True, help="Output CSV filename.")
    args = parser.parse_args()

    asyncio.run(main(args.input, args.output))
