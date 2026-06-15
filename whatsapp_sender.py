import openpyxl
import webbrowser
import urllib.parse
import time

# -----------------------------------------------
# SETTINGS - Change these to match your needs
# -----------------------------------------------
EXCEL_FILE = "contacts.xlsx"   # Put your Excel file name here
MESSAGE = "Hello my friend {name}!"  # {name} will be replaced automatically
DELAY_SECONDS = 3              # Wait time between opening each chat
# -----------------------------------------------

def read_contacts(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    contacts = []
    for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header row
        phone = str(row[0]).strip() if row[0] else ""
        name  = str(row[1]).strip() if row[1] else ""
        if phone and phone != "None":
            # Add India country code if not present
            if not phone.startswith("91") and len(phone) == 10:
                phone = "91" + phone
            contacts.append({"phone": phone, "name": name})
    return contacts

def send_whatsapp(phone, name, message):
    personalized = message.replace("{name}", name)
    encoded_msg  = urllib.parse.quote(personalized)
    url = f"https://wa.me/{phone}?text={encoded_msg}"
    webbrowser.open(url)
    print(f"✅ Opened chat for {name} ({phone})")

def main():
    print("📋 Reading contacts from Excel...")
    contacts = read_contacts(EXCEL_FILE)
    print(f"✅ Found {len(contacts)} contacts\n")

    for i, contact in enumerate(contacts):
        print(f"📤 Sending to {contact['name']} ({contact['phone']})...")
        send_whatsapp(contact["phone"], contact["name"], MESSAGE)
        if i < len(contacts) - 1:
            print(f"   Waiting {DELAY_SECONDS} seconds before next...\n")
            time.sleep(DELAY_SECONDS)

    print(f"\n🎉 Done! Opened {len(contacts)} WhatsApp chats.")
    print("👉 Go to each chat and press SEND in WhatsApp.")

if __name__ == "__main__":
    main()
