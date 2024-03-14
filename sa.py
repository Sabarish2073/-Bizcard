import os
import re
import cv2
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu  # Assuming this is a custom component
import easyocr
import torch

st.set_option('deprecation.showPyplotGlobalUse', False)
# SETTING PAGE CONFIGURATIONS
icon_path = "C:\\Users\\ASUS 502\\OneDrive\\Desktop\\cards\\3.png"
page_title = "BizCardX: Extracting Business Card Data with OCR | By BALAVIGNESH S S"
st.set_page_config(page_title=page_title,
                   page_icon=icon_path,
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={'About': """# This OCR app is created by *BALAVIGNESH S S*!"""})

st.markdown("<h1 style='text-align: center; color: blue;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

# SETTING-UP BACKGROUND IMAGE
def setting_bg():
    st.markdown(f""" <style>.stApp {{
                        background:url("{icon_path}");
                        background-size: cover}}
                     </style>""", unsafe_allow_html=True)

setting_bg()

# CONNECTING WITH POSTGRESQL DATABASE
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="business card",
    user="postgres",
    password="postgresql"
)
cursor = conn.cursor()

# TABLE CREATION
cursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id SERIAL PRIMARY KEY,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image BYTEA
                    )''')

# HOME MENU
selected = option_menu(None, ["Home", "Upload & Extract", "Modify"],
                       icons=["house", "cloud-upload", "pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "-2px",
                                            "--hover-color": "#6495ED"},
                               "icon": {"font-size": "35px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}})

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])

# HOME MENU
if selected == "Home":
    col1 , col2 = st.columns(2)
    with col1:
        st.image(Image.open("S:\\business card\\.venv\\1.png"), width=500)
        st.markdown("## :green[**Technologies Used :**] Python, easy OCR, Streamlit, PostgreSQL, Pandas")
    with col2:
       st.write("## :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
       st.write('## The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')

# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    if st.button(":blue[Already stored data]"):
        cursor.execute("SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
        updated_df = pd.DataFrame(cursor.fetchall(), columns=["Company_Name", "Card_Holder", "Designation", "Mobile_Number", "Email", "Website", "Area", "City", "State", "Pin_Code"])
        st.write(updated_df)

    st.subheader(":blue[Upload a Business Card]")
    uploaded_card = st.file_uploader("Upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])

    if uploaded_card is not None:
        uploaded_cards_dir = "S:\\business card\\.venv\\uploaded_cards"
        uploaded_card_path = os.path.join(uploaded_cards_dir, uploaded_card.name)
        with open(uploaded_card_path, "wb") as f:
            f.write(uploaded_card.read())

        def image_preview(image, res):
            for (bbox, text, prob) in res:
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15, 15)
            plt.axis('off')
            plt.imshow(image)
            st.pyplot()

        image = cv2.imread(uploaded_card_path)
        res = reader.readtext(uploaded_card_path)
        st.markdown("### Image Processed and Data Extracted")
        image_preview(image, res)

        result = reader.readtext(uploaded_card_path, detail=0, paragraph=False)
        data = {"company_name": [], "card_holder": [], "designation": [], "mobile_number": [], "email": [], "website": [], "area": [], "city": [], "state": [], "pin_code": []}

        def get_data(res):
            for ind, i in enumerate(res):
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "@" in i:
                    data["email"].append(i)
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])
                elif ind == len(res) - 1:
                    data["company_name"].append(i)
                elif ind == 0:
                    data["card_holder"].append(i)
                elif ind == 1:
                    data["designation"].append(i)
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)
                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])

        get_data(result)

        def create_df(data):
            df = pd.DataFrame(data)
            return df

        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)

        if st.button("Upload to Database"):
            for i, row in df.iterrows():
                sql = """INSERT INTO card_data(company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code, image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                with open(uploaded_card_path, "rb") as f:
                    binary_data = f.read()
                cursor.execute(sql, (row["company_name"], row["card_holder"], row["designation"], row["mobile_number"], row["email"], row["website"], row["area"], row["city"], row["state"], row["pin_code"], binary_data))
                conn.commit()
            st.success("#### Uploaded to database successfully!")

        if st.button(":blue[View updated data]"):
            cursor.execute("SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
            updated_df = pd.DataFrame(cursor.fetchall(), columns=["Company_Name", "Card_Holder", "Designation", "Mobile_Number", "Email", "Website", "Area", "City", "State", "Pin_Code"])
            st.write(updated_df)

# MODIFY MENU
if selected == "Modify":
    st.subheader(':blue[You can view , alter or delete the extracted data in this app]')
    select = option_menu(None,
                         options=["ALTER", "DELETE"],
                         default_index=0,
                         orientation="horizontal",
                         styles={"container": {"width": "100%"},
                                 "nav-link": {"font-size": "20px", "text-align": "center", "margin": "-2px"},
                                 "nav-link-selected": {"background-color": "#6495ED"}})

    if select == "ALTER":
        st.markdown(":blue[Alter the data here]")

        try:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                st.markdown("#### Update or modify any data below")
                cursor.execute("SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data WHERE card_holder=%s", (selected_card,))
                result = cursor.fetchone()

                company_name = st.text_input("Company_Name", result[0])
                card_holder = st.text_input("Card_Holder", result[1])
                designation = st.text_input("Designation", result[2])
                mobile_number = st.text_input("Mobile_Number", result[3])
                email = st.text_input("Email", result[4])
                website = st.text_input("Website", result[5])
                area = st.text_input("Area", result[6])
                city = st.text_input("City", result[7])
                state = st.text_input("State", result[8])
                pin_code = st.text_input("Pin_Code", result[9])

                if st.button(":blue[Commit changes to DB]"):
                    cursor.execute("""UPDATE card_data SET company_name=%s, card_holder=%s, designation=%s, mobile_number=%s, email=%s, website=%s, area=%s, city=%s, state=%s, pin_code=%s WHERE card_holder=%s""", (company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code, selected_card))
                    conn.commit()
                    st.success("Information updated in database successfully.")

            if st.button(":blue[View updated data]"):
                cursor.execute("SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
                updated_df = pd.DataFrame(cursor.fetchall(), columns=["Company_Name", "Card_Holder", "Designation", "Mobile_Number", "Email", "Website", "Area", "City", "State", "Pin_Code"])
                st.write(updated_df)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    elif select == "DELETE":
        st.markdown(":blue[Delete the data here]")
        try:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                if st.button(":red[Delete]"):
                    cursor.execute("DELETE FROM card_data WHERE card_holder=%s", (selected_card,))
                    conn.commit()
                    st.success("Deleted successfully.")

            if st.button(":blue[View updated data]"):
                cursor.execute("SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
                updated_df = pd.DataFrame(cursor.fetchall(), columns=["Company_Name", "Card_Holder", "Designation", "Mobile_Number", "Email", "Website", "Area", "City", "State", "Pin_Code"])
                st.write(updated_df)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# CLOSE THE CONNECTION
cursor.close()
conn.close()
