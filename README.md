# Telegram Quiz Scraper & Backup Tool

A Python tool to backup quiz questions, correct answers, explanations, tags, and topics from a Telegram channel into a clean CSV (Excel-compatible) file. This was designed with Active Medcall (PH) in mind, but is useful for any Telegram channel hosting quiz questions.

**Key Features:**
* **Automatic Answer Extraction:** Automatically votes on polls to reveal the correct answer and explanation.
* **Smart Merging:** If you run the script again, it updates your existing file with new tags/topics without needing to re-vote (saving time).
* **Resume Capability:** If the script stops, it picks up exactly where it left off.
* **Flood Protection:** Automatically pauses if Telegram asks you to wait (prevents account bans).

---

## 📋 Prerequisites

Before you begin, you need to get two secret keys from Telegram so the script can log in as you.

### Get your Telegram API Credentials
1.  Go to **[my.telegram.org](https://my.telegram.org)** in your web browser.
2.  Enter your phone number (e.g., `+123456789`) and click **Next**.
3.  Telegram will send a confirmation code to your **Telegram App** (not SMS). Enter that code on the website.
4.  Click on **API development tools**.
5.  Fill in the form:
    * **App title:** `QuizBackup` (or any name you want)
    * **Short name:** `quizbackup`
    * **Platform:** Select **Desktop**
    * **URL:** You can leave this blank or type `http://localhost`
6.  Click **Create application**.
7.  **Keep this page open!** You will need the **`App api_id`** and **`App api_hash`** for Step 4.

---

## 🚀 Installation Guide (macOS)

### Step 1: Create a Work Folder
Open the **Terminal** app on your Mac (press `Cmd + Space` and type "Terminal"). Copy and paste these commands one by one, pressing **Enter** after each:

#### Create a new folder on your Desktop (or any folder of your choice)
`mkdir -p ~/Desktop/QuizScraper`

#### Go inside that folder
`cd ~/Desktop/QuizScraper`

### Step 2: Check Python
Macs usually come with Python installed. Check if you have it by running:

`python3 --version`

*If you see an error, download and install Python from [python.org](https://www.python.org/downloads/).*

### Step 3: Install the Library
We use a library called `Telethon` to talk to Telegram. Install it by running:

`pip3 install telethon`

### Step 4: Save the Script
1.  Download the `scraper.py` file from this repository and save it into the `QuizScraper` folder on your Desktop.
2.  **Right-click** `scraper.py` and choose **Open With > TextEdit** (or an editor/IDE of your choice).
3.  Look for this section at the top:
    ```python
    # --- CONFIGURATION ---
    api_id = 'YOUR_API_ID'       
    api_hash = 'YOUR_API_HASH'   
    channel_username = 'YOUR_CHANNEL_LINK' 
    # ---------------------
    ```
4.  Replace `'YOUR_API_ID'` with the number from the Telegram website.
5.  Replace `'YOUR_API_HASH'` with the long code from the Telegram website.
6.  Replace `'YOUR_CHANNEL_LINK'` with the username of the channel (e.g., `'myqbank'` or `'https://t.me/myqbank'`) - the script uses the Active Medcall link by default.
7.  **Save the file** (`Cmd + S`) and close TextEdit/editor.

---

## 🏃‍♂️ How to Run

Go back to your **Terminal**. Make sure you are still in the folder:

cd ~/Desktop/QuizScraper

### Option A: Fresh Start (First Time)
If you have never run the backup before, use this command. It will create a new file called `my_backup.csv`.

python3 scraper.py -o my_backup.csv

* **First Run Note:** The script will ask for your phone number and the login code sent to your Telegram app. This is a one-time login.

### Option B: Update Existing Backup (Smart Merge)
If you already have a file (e.g., `my_backup.csv`) and want to fetch **new questions** or update missing tags, run this:

python3 scraper.py -i my_backup.csv -o my_backup_updated.csv

* `-i`: Input file (your old backup).
* `-o`: Output file (the new, updated file).

> **Tip:** The script acts smart! It will quickly scan old messages to update Tags/Topics without voting, and then slow down to vote on *new* questions only.

---

## 📄 Output Data
The CSV file can be opened in **Excel**, **Numbers**, or **Google Sheets**. It contains:

| Column | Description |
| :--- | :--- |
| **ID** | The unique message ID from Telegram. |
| **Question Number** | The quiz number (e.g., "1367" from "Quiz 1367"). |
| **Topic** | The extracted topic (e.g., "Leprosy"). |
| **Tags** | Hashtags found in the context (e.g., "#Dermatology"). |
| **Question** | The full question text. |
| **Correct Answer** | The text of the correct option. |
| **Explanation** | The "Solution" text (the lamp bulb icon content). |
| **Options 1-4** | The multiple choice options. |

---

## ⚠️ Important Notes

1.  **Voting:** To see the correct answer, the script **must vote** on the poll. It defaults to voting for "Option 1".
    * *Note:* This means your personal Telegram account will show votes for Option 1 on all these historical polls.
2.  **FloodWait:** If you see a message saying `[!] FloodWait: Sleeping 68s...`, **do not panic**.
    * This is Telegram telling the script to slow down. The script will automatically pause and resume safely. Do not close the terminal; just let it wait.
3.  **Privacy:** Your API keys are private. Do not share your `scraper.py` file with others if it contains your keys.

## ⚖️ Disclaimer
This tool is for personal data backup and educational purposes only. Please respect the Terms of Service of Telegram and the content rights of the channel owners.
