from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json


# -------------------------
# CHROME SETUP
# -------------------------
options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # optional

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)


# -------------------------
# STATE / UT CODES
# -------------------------
state_codes = {
    "andhra pradesh": "AP",
    "arunachal pradesh": "AR",
    "assam": "AS",
    "bihar": "BR",
    "chhattisgarh": "CG",
    "delhi": "DL",
    "goa": "GA",
    "gujarat": "GJ",
    "haryana": "HR",
    "himachal pradesh": "HP",
    "jharkhand": "JH",
    "karnataka": "KA",
    "kerala": "KL",
    "madhya pradesh": "MP",
    "maharashtra": "MH",
    "mizoram": "MZ",
    "odisha": "OD",
    "punjab": "PB",
    "rajasthan": "RJ",
    "tamil nadu": "TN",
    "telangana": "TS",
    "uttar pradesh": "UP",
    "uttarakhand": "UK",
    "west bengal": "WB"
}


# -------------------------
# CORE SCRAPER (SMART: DYNAMIC SCROLLS)
# -------------------------
def scrape_all_districts(state_code):
    url = f"https://igod.gov.in/sg/{state_code}/E042/organizations"
    print(f"  Loading {url}...")
    driver.get(url)

    # Wait for initial elements
    wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.search-result-row a.search-title")
        )
    )
    time.sleep(1.5)

    collected = set()
    scroll_attempts = 0
    stable_rounds = 0
    max_stable_rounds = 4  # Stop after 4 consecutive scrolls with no new data
    last_count = 0

    while True:
        scroll_attempts += 1

        # Fresh read each time
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            "div.search-result-row a.search-title"
        )

        before = len(collected)
        for el in elements:
            try:
                txt = el.text.strip().lower()
                if txt:
                    collected.add(txt)
            except Exception:
                continue
        after = len(collected)

        print(
            f"    Scroll {scroll_attempts}: total unique districts = "
            f"{after} (new this scroll: {after - before})"
        )

        # If no new districts found this scroll
        if after == before:
            stable_rounds += 1
            print(f"      → No new data (stable round {stable_rounds}/{max_stable_rounds})")
        else:
            stable_rounds = 0  # Reset if we found new data

        # Stop if we've had max_stable_rounds with no new data
        if stable_rounds >= max_stable_rounds:
            print(f"      → Reached stable state. Stopping scrolling.")
            break

        # Scroll down a screen height
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(2)

        # Optionally wait for any loader/spinner
        try:
            loading_elements = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='loading'], [class*='spinner'], [class*='loader']"
            )
            if loading_elements:
                print(f"      → Loading indicator detected, waiting extra 1s...")
                time.sleep(1)
        except Exception:
            pass

    districts = sorted(list(collected))
    print(f"  ✓ Final count for {state_code}: {len(districts)} districts")
    print(f"  Districts: {districts}")
    return districts


# -------------------------
# MAIN LOOP
# -------------------------
state_district_map = {}
total_states = len(state_codes)
completed = 0

for state, code in state_codes.items():
    completed += 1
    print(f"\n[{completed}/{total_states}] Scraping {state.upper()} ({code}) ...")
    try:
        districts = scrape_all_districts(code)

        state_district_map[state] = {
            "state_code": code,
            "districts": districts,
            "district_count": len(districts),
        }

        # Print per-state summary to terminal
        print(
            f"  → {state} ({code}): {len(districts)} districts"
        )

        time.sleep(1.5)

    except Exception as e:
        print(f"  ✗ Error scraping {state}: {e}")
        state_district_map[state] = {
            "state_code": code,
            "districts": [],
            "district_count": 0,
            "error": str(e),
        }


# -------------------------
# SAVE JSON + TERMINAL OUTPUT
# -------------------------
output_file = "state_district_reference.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(state_district_map, f, indent=2, ensure_ascii=False)

driver.quit()

print("\n" + "=" * 70)
print("✅ SCRAPING COMPLETE")
print("=" * 70)

total_districts = sum(
    data["district_count"] for data in state_district_map.values()
)
total_states_success = sum(
    1 for data in state_district_map.values() if data["district_count"] > 0
)

print(f"\nStates processed: {total_states_success}/{total_states}")
print(f"Total districts found: {total_districts}")
print(f"Output saved to: {output_file}\n")

print("\n📊 STATE-BY-STATE SUMMARY:\n")
for state, data in state_district_map.items():
    print(f"{state.upper():25} | Code: {data['state_code']:3} | Districts: {data['district_count']:2}")

print("\n" + "=" * 70)
print("\n🔍 FULL JSON OUTPUT:\n")
print(json.dumps(state_district_map, indent=2, ensure_ascii=False))
