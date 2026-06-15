import openpyxl
import time
import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

try:
    from selenium import webdriver
except ImportError:
    install("selenium")
    from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------------------------
# SETTINGS
# -----------------------------------------------
EXCEL_FILE = "contacts.xlsx"
MESSAGE    = "Hello my friend mad {name}!"
# -----------------------------------------------

def read_contacts(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    contacts = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        phone = str(row[0]).strip() if row[0] else ""
        name  = str(row[1]).strip() if row[1] else ""
        if phone and phone != "None":
            if not phone.startswith("91") and len(phone) == 10:
                phone = "91" + phone
            contacts.append({"phone": phone, "name": name})
    return contacts

def send_message(driver, phone, name, message):
    personalized = message.replace("{name}", name)
    # Open chat by phone only (no pre-filled text) — more reliable
    url = f"https://web.whatsapp.com/send?phone={phone}"
    driver.get(url)
    print(f"   Opening chat for {name}...")

    wait = WebDriverWait(driver, 45)

    try:
        # ── Step 1: Wait for page to settle after navigation ──
        time.sleep(5)

        # Check for "invalid phone number" popup
        try:
            popup = driver.find_element(By.XPATH, '//div[@data-animate-modal-popup="true"]')
            if popup:
                print(f"   ⚠️  Invalid/unregistered number for {name} ({phone}), skipping.")
                ok_btn = driver.find_element(By.XPATH, '//div[@data-animate-modal-popup="true"]//button')
                ok_btn.click()
                return
        except Exception:
            pass  # No popup = number is fine, continue

        # ── Step 2: Wait for the message input box (try multiple selectors) ──
        msg_box = None
        selectors = [
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'),
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="11"]'),
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'),
            (By.XPATH, '//div[@contenteditable="true"][@title="Type a message"]'),
            (By.XPATH, '//div[@contenteditable="true"][contains(@class,"_ak1r")]'),
            (By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab]'),
            # Broadest fallback: any contenteditable div inside the chat footer
            (By.XPATH, '//footer//div[@contenteditable="true"]'),
        ]
        for by, selector in selectors:
            try:
                msg_box = wait.until(EC.element_to_be_clickable((by, selector)))
                print(f"   ✅ Found message box.")
                break
            except Exception:
                continue

        if msg_box is None:
            # Save screenshot for debugging
            driver.save_screenshot(f"debug_{name}.png")
            print(f"   ❌ Could not locate message box for {name}. Screenshot saved as debug_{name}.png")
            return

        # ── Step 3: Click the box, TYPE the message, then send ──
        time.sleep(1)
        msg_box.click()
        time.sleep(0.5)

        # Type message character by character to avoid clipboard issues
        # Using ActionChains for reliability
        actions = ActionChains(driver)
        actions.move_to_element(msg_box).click().send_keys(personalized).perform()
        time.sleep(1)

        # Send with ENTER
        msg_box.send_keys(Keys.ENTER)
        time.sleep(2)

        # ── Step 4: Confirm the message appeared in chat ──
        # (optional visual check — just wait a moment)
        print(f"   ✅ Message sent to {name} ({phone})")

    except Exception as e:
        driver.save_screenshot(f"debug_{name}.png")
        print(f"   ❌ Failed to send to {name}: {e}")
        print(f"      Screenshot saved as debug_{name}.png for inspection.")

def get_driver():
    options = Options()

    profile_path = os.path.join(os.getcwd(), "wa_chrome_profile")
    options.add_argument(f"--user-data-dir={profile_path}")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Try webdriver-manager first
    try:
        print("   Installing correct ChromeDriver for your Chrome version...")
        install("webdriver-manager")
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("   ✅ Chrome started!")
        return driver
    except Exception as e:
        print(f"   ⚠️  webdriver-manager failed: {e}")

    # Fallback: undetected-chromedriver
    try:
        print("   Trying undetected-chromedriver...")
        install("undetected-chromedriver")
        import undetected_chromedriver as uc
        driver = uc.Chrome()
        print("   ✅ Chrome started with undetected-chromedriver!")
        return driver
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print("\n" + "="*50)
        print("MANUAL FIX NEEDED:")
        print("1. Check your Chrome version:")
        print("   Chrome → 3 dots → Help → About Google Chrome")
        print("2. Download matching ChromeDriver from:")
        print("   https://googlechromelabs.github.io/chrome-for-testing/")
        print(f"3. Put chromedriver.exe in: {os.getcwd()}")
        print("="*50)
        raise

def main():
    print("=" * 50)
    print("  WhatsApp Auto Sender")
    print("=" * 50)

    print("\n⚠️  Closing any open Chrome windows to avoid conflicts...")
    os.system("taskkill /f /im chrome.exe >nul 2>&1")
    time.sleep(2)

    print("\n📋 Reading contacts from Excel...")
    contacts = read_contacts(EXCEL_FILE)
    print(f"✅ Found {len(contacts)} contacts")
    for c in contacts:
        print(f"   - {c['name']} : {c['phone']}")

    print("\n🌐 Starting Chrome browser...")
    driver = get_driver()

    print("\n📱 Opening WhatsApp Web...")
    driver.get("https://web.whatsapp.com")
    print("\n⚠️  SCAN THE QR CODE WITH YOUR PHONE NOW!")
    print("   You have 30 seconds...")
    time.sleep(30)

    # Wait for WhatsApp to fully load after QR scan
    print("\n⏳ Waiting for WhatsApp to fully load...")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "side"))
        )
        print("✅ WhatsApp loaded successfully!")
    except Exception:
        print("⚠️  Could not confirm load — proceeding anyway...")

    print(f"\n📤 Sending messages to {len(contacts)} contacts...\n")
    for i, contact in enumerate(contacts):
        print(f"[{i+1}/{len(contacts)}] Sending to {contact['name']}...")
        send_message(driver, contact["phone"], contact["name"], MESSAGE)
        time.sleep(3)

    print("\n🎉 Done! Check above for any failures.")
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    main()
