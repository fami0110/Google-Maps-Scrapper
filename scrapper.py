import os
import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import json
import re
from tqdm import tqdm

def querySelector(rel, selector):
    return rel.find_element(By.CSS_SELECTOR, selector)

def querySelectorAll(rel, selector):
    return rel.find_elements(By.CSS_SELECTOR, selector)


def scrap(url, img_amount = 0):
    global driver

    driver.get(url)

    name = None
    rate = None
    address = None
    contact = None
    latitude = None
    longitude = None
    price_min = None
    price_max = None
    schedules = {}
    images = []

    print("\nSTATUS: Get Place Name...")
    try:
        e_name = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf.lfPIob"))
        )
        name = e_name.get_attribute('innerText').strip()

        print("FOUND:", name)
    except:
        print('Failed to Get Name!')
        

    print("\nSTATUS: Get Place Rate...")
    try:
        e_rate = querySelector(driver, 'div.F7nice span[aria-hidden="true"]')
        rate = float(e_rate.get_attribute('innerText').strip().replace(',', '.'))

        print("FOUND:", rate)
    except:
        print('Failed to Get Rate!')


    print("\nSTATUS: Get Place Address...")
    try:
        e_address = querySelector(driver, 'button.CsEnBe[data-item-id="address"]')
        address = e_address.get_attribute('aria-label').strip()

        print("FOUND:", address)
    except:
        print('Failed to Get Address!')

    
    print("\nSTATUS: Get Place Contact...")
    try:
        span = querySelector(driver, 'span.google-symbols.NhBTye.PHazN')
        parent = span.find_element(By.XPATH, "./ancestor::div[@class='AeaXub']")
        e_contact = querySelector(parent, 'div.Io6YTe')
        contact = e_contact.get_attribute('innerText')

        print("FOUND:", contact)
    except:
        print("Failed to Get Contact!")


    print("\nSTATUS: Get Place Schedules...")
    try:
        table_rows = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.eK4R0e tr'))
        )
        for row in table_rows:
            e_day = querySelector(row, "td.ylH6lf div")
            e_hours = querySelector(row, "td.mxowUb li")
            day = e_day.get_attribute('innerText')
            hours = e_hours.get_attribute('innerText')
            
            if "Tutup" in hours: continue

            time = hours.split('–')
            
            schedules[day] = {
                'time-start': time[0],
                'time-end': time[1],
            }

        print("FOUND:", schedules)
    except:
        print("Failed to Get Schedules!")
    
    
    try:
        print("\nSTATUS: Get Place Pricelist...")

        table_rows = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.rqRH4d tr'))
        )
        all_polling = []

        for row in table_rows:
            pricelist = querySelector(row, "td.fsAi0e").get_attribute('innerText')[3:].replace('.', '').split('–')
            polling = int(querySelector(row, 'span.QANbtc').get_attribute('aria-label')[:-1]) 
            all_polling.append({
                "pricelist" : pricelist, 
                "polling" : polling
            })

        most_polling = sorted(all_polling, key=lambda x: x['polling'])

        price_min = int(most_polling[0]['pricelist'][0])
        price_max = int(most_polling[0]['pricelist'][1])

        print("FOUND:", [price_min, price_max])
    except:
        print("Failed to Get Pricelist!")


    print("\nSTATUS: Get Coordinate...")
    try:
        current_url = driver.current_url
        match = re.search(r"@(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(\d+)z", current_url)

        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(3))
        else:
            raise Exception()
        
        print("FOUND:", [longitude, latitude])
    except:
        print('Failed to Get Coordinate')

    if img_amount != 0:
        print("\nSTATUS: Get Images Sources...")

        try:
            link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.aoRNLd.kn2E5e.NMjTrf.lvtCsd'))
            )
            link.click()

            image_containers = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde > div > div"))
            )

            for i in range(img_amount):
                driver.execute_script("document.querySelector('div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde').scrollBy(0, window.innerHeight)")
                sleep(0.2)

                div = WebDriverWait(image_containers[i], 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.OKAoZd > div.U39Pmb > .Uf0tqf.loaded'))
                )
                src = div.get_attribute('style').strip().split('"')[1]

                images.append(src)
            
            print("FOUND:", images)
        except:
            print("Failed to Get Image Sources!")

    return {
        "name": name,
        "address": address,
        "link": url,
        "contact": contact,
        "longitude": longitude,
        "latitude": latitude,
        "price_min": price_min,
        "price_max": price_max,
        "schedules": schedules,
        "rate": rate,
        "images": images,
    }

def main():
    global driver

    links = None
    img_amount = 0

    if (len(sys.argv) > 1):
        argvs = sys.argv[1:]

        for i in range(len(argvs)):
            if argvs[i] == '-h':
                print("Usage: python scrapper.py [-L FILE] [-a IMG_AMOUNT]")
                sys.exit(1)
            if argvs[i] == '-L':
                i += 1
                sc = argvs[i]
                lines = open(sc, 'r').readlines()
                links = [line.strip() for line in lines]  
            elif argvs[i] == '-a':
                i += 1
                img_amount = int(argvs[i])

    result = []

    if not links or len(links) == 0:
        url = input('Google Maps Link = ')
        img_amount = int(input('Image Amount     = '))
        
        driver = webdriver.Chrome()

        print(f"\n=========== USING ============= \nURL    = {url} \nAmount = {img_amount}")
        print("========== SCRAPPING ==========")

        res = scrap(url, img_amount)
        result.append(res)
    else:
        driver = webdriver.Chrome()

        for url in links:
            print(f"\n=========== Using ============ \nURL    = {url} \nAmount = {img_amount}")
            print("========== SCRAPPING ==========")
            
            res = scrap(url, img_amount)
            result.append(res)

    driver.quit()

    print("\n======== END SCRAPPING ========")


    print("\nProcess Data & Download Images...")
    os.makedirs('result', exist_ok=True)

    for item in tqdm(result):
        # Make Directory
        place_folder = os.path.join('result', item['name'])
        os.makedirs(place_folder, exist_ok=True)

        # Store data json
        images = item['images']
        del item['images']
        data = json.dumps(item, indent=4)
        json_path = os.path.join(place_folder, 'data.json')
        open(json_path, 'w').write(data)
        
        # Download Images
        for i, src in enumerate(images):
            response = requests.get(src)
            if response.status_code == 200:
                image_path = os.path.join(place_folder, f'{i+1}.jpg')
                open(image_path, 'wb').write(response.content)

main()