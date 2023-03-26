import os
import random
from datetime import datetime, timedelta
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import os

def scrap_bocznica():
    filename = f"data//Scrapping_{datetime.now().strftime('%m-%d-%y_%H-%M-%S')}"
    #browse site and get table with all trains
    driver = webdriver.Chrome('chromedriver')
    driver.get('http://bocznica.eu/trains')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'//table[@width = "100%"]' )))
    element = driver.find_element(By.XPATH,'//table[@width = "100%"]' )
    html_table = element.get_attribute("outerHTML")
    df_all_trains = pd.read_html(html_table, encoding='utf-8', header= 0 )[0]

    train_ids = df_all_trains["Pociąg"]
    cols = ["nazwa_pociagu", "stacja_poczatkowa", "stacja_koncowa", "stacja_pomiaru", "data", "czas_rozkladowy", "czas_przyjazdu", "opoznienie"] 

    for name in train_ids:
        driver.implicitly_wait(random.random())

        #go to train site
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//*[contains(text(), "{name}") ]' )))
        button = driver.find_element(By.XPATH, f'//*[contains(text(), "{name}") ]')
        button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'//table[@width = "100%"]' )))
        element = driver.find_element(By.XPATH,'//table[@width = "100%"]' )
        html_train_table = element.get_attribute("outerHTML")
        df_train = pd.read_html(html_train_table, encoding='utf-8', header= 0 )[0]

        
        #cols = [ "stacja_poczatkowa", "stacja_koncowa", "stacja_pomiaru", "data", "czas_rozkladowy","czas przyjazdu" ,"opoznienie"]
        start_station = df_train["Stacja"].iloc[0]
        end_station = df_train["Stacja"].iloc[-1]
        
        for column in list(df_train)[2:]:
            if column != datetime.now().strftime('%d.%m'):
                for index in range(0,len(df_train)):
                    df_train_formated = pd.DataFrame(columns=cols)
                    schedule_time = datetime.strptime(df_train["Czas"][index], "%H:%M")
                    delay = df_train[column][index]
                    if delay != '--':
                        arrival_time = schedule_time + timedelta(minutes=int(delay))
                    values = [name, start_station, end_station, df_train["Stacja"][index], column, schedule_time.strftime("%H:%M"),
                            arrival_time.strftime("%H:%M"), delay ]
                    row = dict(zip(cols, values))
                    df_train_formated = df_train_formated.append(row, ignore_index=True) 

                    # if file does not exist write header 
                    if not os.path.isfile(filename  + ".csv"):
                        df_train_formated.to_csv(filename + ".csv", header=cols, index = False, encoding="utf-8-sig")
                    else: 
                        df_train_formated.to_csv(filename + ".csv", mode='a', header=False, index = False, encoding="utf-8-sig")

        driver.back()

def connect_data():
    files  = os.listdir("data/scrapped_data/")
    for index in range(len(files)):
        if index == 0:
            df = pd.read_csv("data/scrapped_data/" + files[index])
        else:
            df_temp = pd.read_csv("data/scrapped_data/" + files[index])
            df = pd.concat([df, df_temp]).drop_duplicates().reset_index(drop=True)

    df.to_csv(f"data/data_updated.csv")
    


    

if __name__ == "__main__":
    scrap_bocznica()
    connect_data()