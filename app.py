import os
import subprocess
import base64
import logging
import clipboard
import pandas as pd
import streamlit as st
from datetime import timedelta, datetime

# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

from data_processing import process_data, check_missing_branches

def setup():
    """Sets up logging and Streamlit page configuration."""

    # Ensure log folder exists
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
    )
    file_handler = logging.FileHandler("logs.log")  # Create the file handler
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    try:
        # Update the package list
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "xclip"])
        subprocess.run(["sudo", "apt-get", "install", "xselect"])
        logger.info("xclip installed successfully!")
    except subprocess.CalledProcessError as e:
        logger.info(f"Error updating linux package: {e}")

    # Set up the Streamlit page layout and title
    st.set_page_config(
        page_title="Abdullah AlOthaim Markets Egypt",
        layout="wide", initial_sidebar_state="auto", 
        page_icon='./assests/logo.png'
        )

    # Centered title for the app
    st.markdown(
        "<h1 style='text-align: center;'>Abdullah AlOthaim Markets Egypt</h1>", 
        unsafe_allow_html=True
        )

def upload_excel_file():
    """Handles file upload and returns the uploaded file."""
    with st.container():
        st.subheader("Upload Excel File")
        st.caption("This file should be extracted from `Upload Sessions` screen from Dynamics 365.")

        # File uploader for Excel files
        uploaded_file = st.file_uploader(
            "Upload Excel File", type=["xlsx"],
            help="Drag and drop file here or click to upload.",
            label_visibility="hidden", accept_multiple_files=False,
        )
        return uploaded_file
       

def display_results(all_branches_df, missed_branches_df):
    """Displays the analysis results in the Streamlit app."""
    with st.container():
        # Create two columns for layout
        left_col, right_col = st.columns([1, 1])

        with left_col:
            # Display Uploaded Branches
            st.write(" ")
            st.write(" ")

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.subheader(f"Uploaded Branches", divider="green")  
            st.caption(f"{current_time}")
            st.markdown(
                f"<div class='uploaded-branches-box'>{len(all_branches_df[all_branches_df['flag']==0])}</div>",
                unsafe_allow_html=True,
            )


            # Highlight rows with time difference greater than 30 minutes
            styled_results_df = all_branches_df.style.apply(
                lambda x: [ "background-color: rgba(255, 255, 0, 0.2)"  if x["flag"] == 1 else "" 
                            for _ in range(len(x)) ], axis=1,
            )

            # Display the styled DataFrame
            st.dataframe(styled_results_df, use_container_width=False, hide_index=True)

            # Streamlit button to copy DataFrame content to clipboard
            if st.button("Copy", key="copy_button", use_container_width=False):
                
                clipboard.copy(all_branches_df.drop("flag", axis=1).to_csv(sep="\t", index=False))
                st.success("Data copied to clipboard! ")

        with right_col:
            # Display Missed Branches
            st.write(" ")
            st.write(" ")
            st.subheader("Missed Branches", divider="red")
            st.caption(f"{current_time}")
            st.markdown(
                f"<div class='missed-branches-box'>{len(missed_branches_df)}</div>",
                unsafe_allow_html=True,
            )
            
            # Display "Missed Branches" table if there are any missed branches
            if len(missed_branches_df) > 0:
                st.dataframe(missed_branches_df, use_container_width=False, hide_index=True)
            else:
                st.markdown(
                    "<h1 style='text-align: center; font-size: 32px;'>\n\n All Branches Uploded the Sales!</h1>",
                    unsafe_allow_html=True,
                )

                # st.markdown('<img src="./assests/celeberation.gif"/>', unsafe_allow_html=True)
                file_ = open("./assests/celeberation.gif", "rb")
                contents = file_.read()
                data_url = base64.b64encode(contents).decode("utf-8")
                file_.close()

                st.markdown(
                    f'<div style="text-align:center"><img src="data:image/gif;base64,{data_url}" alt="gif"></div>',
                    unsafe_allow_html=True,
                )
    # Button to send the email
    # if st.button("Send Email", disabled=all_branches_df is None or missed_branches_df is None):
    #     if all_branches_df is not None and missed_branches_df is not None:
    #         send_email(all_branches_df, missed_branches_df)


# def send_email(all_branches_df, missed_branches_df):
    # """Sends an email with analysis results using SMTP."""

    # # Email configuration
    # SERVER = "smtp.othaimmarkets.com.eg"  # Replace with your SMTP server
    # FROM = "heba.mohamed@othaimmarkets.com.eg"  # Replace with your email address
    # TO = ["itops@othaimmarkets.com.eg"]  # Replace with recipient email(s)

    # SUBJECT = "Branch Status Report"
    # TEXT = f"""
    # ## Uploaded Branches:

    # {tabulate(all_branches_df.drop("flag", axis=1), tablefmt="plain", headers="keys", showindex=False)}

    # ## Missed Branches:

    # {tabulate(missed_branches_df, tablefmt="plain", headers="keys", showindex=False)}
    # """

    # # Create message object
    # msg = MIMEMultipart()
    # msg["From"] = FROM
    # msg["To"] = ", ".join(TO)
    # msg["Subject"] = SUBJECT
    # msg.attach(MIMEText(TEXT, 'plain'))

    # # Send the email
    # with smtplib.SMTP_SSL(SERVER, 465) as server:  # Use SMTP_SSL for secure connections
    #     server.login(FROM, "H@M2024*")  # Replace with your email password
    #     server.sendmail(FROM, TO, msg.as_string())
    #     server.quit()

    # st.success("Email sent successfully!")
    # logging.info("Email sent successfully.")

def main():
    """Main function to run the Streamlit app."""

    # File Upload Section
    uploaded_file = upload_excel_file()

    if uploaded_file is not None:
        # Process uploaded data and handle errors
        try:
            results_df = process_data(uploaded_file)
            logging.info("Data successfully processed.")
        
        except ValueError as e:
            logging.warning(f"Error processing file: {e}")
            st.error("Error processing file")
            return
        
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            st.error("Error processing file")
            return

        try:
            all_branches_df, missed_branches_df = check_missing_branches(results_df)
            logging.info("Branch status analysis complete.")
        except Exception as e:
            logging.error(f"Error while checking missing branches : {e}")
            st.error("Error while checking missing branches")
            return

        # Display Results Section
        display_results(all_branches_df, missed_branches_df)

if __name__ == "__main__":

    setup()

    # Include CSS from a separate file (style.css)
    with open("style.css") as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

    main()
