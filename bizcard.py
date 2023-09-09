import pymysql as mysql
import streamlit as st
import pandas as pd
import easyocr
import cv2
import numpy as np

# Database connection
try:
    connection = mysql.connect(
        host='localhost',
        database='Bizcard_extract',
        user='root',
        password='lkjhgfdsa@1'
    )

    cur = connection.cursor()

    # Create a table to store business card information
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS Business_card_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name TEXT,
            position TEXT,
            address TEXT,
            pincode VARCHAR(25),
            phone VARCHAR(25),
            email TEXT,
            website TEXT,
            company TEXT
        )'''
    cur.execute(create_table_query)

except mysql.Error as e:
    st.error(f"Error in database connection: {e}")

# EasyOCR reader
reader = easyocr.Reader(['en'])

# Streamlit page configuration
st.set_page_config(page_title='Bizcard', layout='wide')
#st.title('Bizcard Data Extraction using EasyOCR')

st.markdown(
    """
    <style>
    .header {
        background-color: #FFA500;
        padding: 5px;
        border-radius: 5px;
        text-align: center;
        color: red;
    }
    </style>
    <div class="header">
        <h1>Bizcard Data Extraction</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar navigation
page_options = ['Upload Data', 'Show Data', 'Edit Info', 'Delete Data']
selected_page = st.sidebar.radio('Select an option', page_options)


if selected_page == 'Upload Data':
    st.sidebar.markdown('### Upload Card Image')
    file_upload = st.sidebar.file_uploader("Upload card image", type=["jpg", "jpeg", "png", "tiff", "tif", "gif"])

    if file_upload:
        # Read the image using OpenCV
        image = cv2.imdecode(np.fromstring(file_upload.read(), np.uint8), 1)

        # Display the uploaded image
        st.image(image, caption='Uploaded Successfully', use_column_width=True)

        # Button to extract information from the image
        if st.sidebar.button('Extract Data'):
            try:
                bsc = reader.readtext(image, detail=0)
                if len(bsc) == 8:
                    name, position, address, pincode, phone, email, website, company = bsc

                    # Insert the extracted information into the database
                    sql_data = "INSERT INTO Business_card_data (name, position, address, pincode, phone, email, website, company) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    values = (name, position, address, pincode, phone, email, website, company)
                    cur.execute(sql_data, values)
                    connection.commit()

                    # Display success message
                    st.success("Data Inserted")
                else:
                    st.warning("Failed to extract data from the image. Please try another image.")

            except Exception as e:
                st.error(f"Error extracting data from the image: {e}")

elif selected_page == 'Show Data':
    try:
        cur.execute("SELECT * FROM Business_card_data")
        result = cur.fetchall()
        if result:
            df = pd.DataFrame(result, columns=['ID', 'Name', 'Position', 'Address', 'Pincode', 'Phone', 'Email', 'Website', 'Company'])
            st.dataframe(df)
        else:
            st.warning("No business card data available.")

    except mysql.Error as e:
        st.error(f"Error executing SQL query: {e}")

elif selected_page == 'Edit Info':
    # Create a dropdown menu to select a business card to edit
    cur.execute("SELECT id, name FROM Business_card_data")
    result = cur.fetchall()
    business_cards = {row[1]: row[0] for row in result}

    if not business_cards:
        st.warning("No business cards found for editing.")
    else:
        select_card_name = st.selectbox("Select Card To Edit", list(business_cards.keys()))

        # Get the current information for the selected business card
        cur.execute("SELECT * FROM Business_card_data WHERE name=%s", (select_card_name,))
        result = cur.fetchone()

        # Get edited information
        if result is not None:
            name = st.text_input("Name", result[1])
            position = st.text_input("Position", result[2])
            address = st.text_input("Address", result[3])
            pincode = st.text_input("Pincode", result[4])
            phone = st.text_input("Phone", result[5])
            email = st.text_input("Email", result[6])
            website = st.text_input("Website", result[7])
            company = st.text_input("Company_Name", result[8])

            # Create a button to update the business card
            if st.button("Update Data"):
                try:
                    # Update the information for the selected business card in the database
                    cur.execute(
                        "UPDATE Business_card_data SET name=%s, position=%s, address=%s, pincode=%s, phone=%s, email=%s, website=%s, company=%s WHERE name=%s",
                        (name, position, address, pincode, phone, email, website, company, select_card_name))
                    connection.commit()
                    st.success("Card Data Updated")
                except mysql.Error as e:
                    st.error(f"Error updating data: {e}")

if selected_page == 'Delete Data':

    # Create a dropdown menu to select a business card to delete
    cur.execute("SELECT id, name FROM Business_card_data")
    result = cur.fetchall()
    business_cards = {}

    for row in result:
        business_cards[row[1]] = row[0]
    select_card_name = st.selectbox("Select Card To Delete", list(business_cards.keys()))

    # Create a button to delete the selected business card
    if st.button("Delete Card"):
        # Delete the selected business card from the database
        cur.execute("DELETE FROM Business_card_data WHERE name=%s", (select_card_name,))
        connection.commit()
        st.success("Card Data Deleted")


# Close database connection
cur.close()
connection.close()
