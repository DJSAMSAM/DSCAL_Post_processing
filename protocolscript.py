import os
from os import rename

import pymupdf
from tkinter import Tk, filedialog
from pathlib import Path
from pypdf import PdfWriter, PdfReader
import re

# Function to prompt the user to select a folder
def select_folder():
    """
    Prompts the user for a folder to work on
    """
    Tk().withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder with PDF Files")
    if not folder_path:
        print("No folder selected. Exiting...")
        exit()
    return folder_path


def detect_sirius(pdf_folder_path):
    """
    Detects if the string 'sirius' is present on the first page of any PDF in the given folder.
    Returns 1 if 'sirius' is found in any PDF, otherwise returns 0.
    Only Sirius need merging of pdf´s therefore this is required

    Arguments:
    pdf_folder_path (str): Path to the folder containing PDF files.

    Returns:
    int: 1 if 'sirius' is found in any PDF, 0 otherwise.
    """
    try:
        # Iterate through all PDF files in the folder
        for filename in os.listdir(pdf_folder_path):
            if filename.lower().endswith(".pdf"):  # Check if the file is a PDF
                pdf_path = os.path.join(pdf_folder_path, filename)

                # Open the PDF file using PyMuPDF (fitz)
                doc = pymupdf.open(pdf_path)

                # Get the text of the first page
                page = doc.load_page(0)  # Only process the first page
                text = page.get_text("text")  # Extract text in simple text format
                #print(text)
                # Check if "sirius" is in the extracted text (case insensitive)
                if "sirius" in text.lower():  # Using lower() to make the search case-insensitive
                    #print('Sirius detected')
                    return 1  # Return 1 if "sirius" is found in any PDF


        # If no "sirius" is found in any of the PDFs, return 0
        return 0

    except Exception as e:
        print(f"Error processing PDF folder: {e}")
        return 0


def extract_slot_and_flags(pdf_path):
    """
    Extracts the 'slot' value and checks if the PDF contains 'as-found', 'as-left', or 'found-left'.

    Also returns customer ID and Serial number, in case of sirius only the system sn as mmodule SN is superfluous

    Arguments:
    pdf_path (str): Path to the PDF file.

    Returns:
    tuple: (slot_value, as_found, as_left, found_left)
            - slot_value (int): The slot value (integer or 0 if not found),
            - as_found (bool): True if "as-found" is present,
            - as_left (bool): True if "as-left" is present,
            - found_left (bool): True if "found-left" is present.
            - unit_id (string)
            -serial_number (string)
    """
    try:
        # Open the PDF file using PyMuPDF (fitz)
        doc = pymupdf.open(pdf_path)

        # Get the text of the first page
        page = doc.load_page(0)  # Only process the first page
        text = page.get_text("text")  # Extract text in simple text format

        # Initialize flags for "as-found", "as-left", and "found-left"
        as_found = "as-found" in text.lower()
        as_left = "as-left" in text.lower()
        found_left = "found-left" in text.lower()

        # Try to find the slot value (integer above the line containing "Slot")
        #Starts by looking for the first SN, SN of some misc. equipment appears later in protocol,
        #but breaking out of loop only finds first SN
        slot_value = 0  # Default value if no slot is found
        unit_id = ""
        serial_number = ""
        lines = text.split('\n')
        for i in range(1, len(lines)):
            if "Serial number" in lines[i]:
                serial_number = lines[i - 1]
                break
        for i in range(1, len(lines)):  # Start from line 1 (so we can check the previous line)
            if "Slot" in lines[i]:
                # The slot value is in the line above
                previous_line = lines[i - 1].strip()
                try:
                    # Try to extract an integer from the previous line
                    slot_value = int(previous_line)
                    #break  # Stop searching once the slot value is found
                except ValueError:
                    # If no integer in the previous line, continue searching
                    continue
            if "Customer unit ID" in lines[i]:
                #Customer id is in line above
                unit_id = lines[i-1]

            if "System SN" in lines[i]:
                #Overwrites serial number with system SN, in case of sirius system
                serial_number = lines[i - 1]


        return slot_value, as_found, as_left, found_left , unit_id , serial_number

    except Exception as e:
        print(f"Error extracting data from PDF: {e}")
        return 0, False, False, False, "", ""


def merge_pdfs_by_slot_and_flag(pdf_folder_path,output_folder):
    """
    Merges PDFs from a folder, sorting them by 'slot' value and differentiating them by flag ('as-found', 'as-left', 'found-left').

    Arguments:
    pdf_folder_path (str): Path to the folder containing PDF files.
    output_folder (str): Path to the folder where merged PDFs will be saved.

    Returns:
    None
    """
    # Dictionary to hold PDFs by flags (as-found, as-left, found-left)
    merged_pdfs = {
        'as_found': [],
        'as_left': [],
        'found_left': [] ,
        'no_flag': []
    }

    try:
        # Iterate through all PDF files in the folder
        for filename in os.listdir(pdf_folder_path):
            if filename.lower().endswith(".pdf"):  # Check if the file is a PDF
                pdf_path = os.path.join(pdf_folder_path, filename)

                # Extract slot and flag information
                slot_value, as_found, as_left, found_left, _ ,_ = extract_slot_and_flags(pdf_path)

                # Add the PDF to the appropriate list based on the flag
                if as_found:
                    merged_pdfs['as_found'].append((slot_value, pdf_path))
                elif as_left:
                    merged_pdfs['as_left'].append((slot_value, pdf_path))
                elif found_left:
                    merged_pdfs['found_left'].append((slot_value, pdf_path))
                else:
                    merged_pdfs['no_flag'].append((slot_value,pdf_path))

        # Function to merge PDFs sorted by slot
        def merge_and_save_pdfs(pdf_list, output_filename):
            pdf_writer = PdfWriter()
            # Sort PDFs by slot value
            sorted_pdfs = sorted(pdf_list, key=lambda x: x[0])  # Sort by slot value (x[0] is the slot value)
            for _, pdf_path in sorted_pdfs:
                pdf_reader = PdfReader(pdf_path)
                # Add all pages from this PDF
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            # Save the merged PDF
            with open(output_filename, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
            #print(f"Merged PDF saved to: {output_filename}")

        # Merge and save the PDFs for each flag group
        if merged_pdfs['as_found']:
            output_path = os.path.join(output_folder, "merged_as_found.pdf")
            merge_and_save_pdfs(merged_pdfs['as_found'], output_path)

        if merged_pdfs['as_left']:
            output_path = os.path.join(output_folder, "merged_as_left.pdf")
            merge_and_save_pdfs(merged_pdfs['as_left'], output_path)

        if merged_pdfs['found_left']:
            output_path = os.path.join(output_folder, "merged_found_left.pdf")
            merge_and_save_pdfs(merged_pdfs['found_left'], output_path)

        if merged_pdfs['no_flag']:
            output_path = os.path.join(output_folder, "merged_no_flag.pdf")
            merge_and_save_pdfs(merged_pdfs['no_flag'], output_path)
    except Exception as e:
        print(f"Error processing PDF folder: {e}")

def post_process_pdfs(folder_path,merged):
    """
    Calls the 'rename_pdfs' function for all PDFs in the folder if merged is false, and if merged is True
    only the merged files are renamed

    Parameters:
    - folder_path (str): Path to the folder containing PDFs.
    - merged(bool): Information about if contents of folder are merged or not.
    """

    for filename in os.listdir(folder_path):
        if not merged: #if not merged, just send the fike to be renamed
            pdf_path = os.path.join(folder_path, filename)
            rename_pdf(folder_path,filename)
            continue
        elif filename.endswith(".pdf") and "merged" in filename.lower(): #if merged, send only "merged" files to be renamed
            pdf_path = os.path.join(folder_path, filename)
            rename_pdf(folder_path,filename)  # Call the rename_pdfs function on each matched file



def rename_pdf(folder_path,filename):
    """
    Renames PDF with filename at location folder_path based on data inside the PDF which is retrieves with
    extract_slot_and_flags


    :param folder_path:
    :param filename:
    :return: returns nothing, acts on the files in folder_path
    """
    pdf_path = os.path.join(folder_path, filename)
    _, as_found, as_left, found_left , unit_id , serial_number = extract_slot_and_flags(pdf_path)
    cleaned_unit_id=re.sub(r'[<>:"/\\|?*].*', '', unit_id)
    if len(cleaned_unit_id)>>0:
        cleaned_unit_id = cleaned_unit_id + "_"

    suffix=""
    if as_found:
        suffix="_As-found"
    elif as_left:
        suffix="_As-left"
    elif found_left:
        suffix="_Found-left"

    new_filename=f"{cleaned_unit_id}{serial_number}{suffix}.pdf"
    new_path = os.path.join(folder_path, cleaned_unit_id + serial_number + suffix + ".pdf")

    index = 1
    while True:
        try:
            os.rename(pdf_path, new_path)
            print("File "+filename+" renamed to "+new_filename)
            break  # Exit the loop if renaming is successful
        except FileExistsError:
            # If file already exists, modify the filename by appending an index
            new_filename = f"{cleaned_unit_id}{serial_number}{suffix}_{index}.pdf"
            new_path = os.path.join(folder_path, new_filename)
            index += 1  # Increment the index number for the next attempt

# Main execution
if __name__ == "__main__":
    folder_path = select_folder()  # Get folder from user
    is_sirius=detect_sirius(folder_path)
    if is_sirius:
        merge_pdfs_by_slot_and_flag(folder_path,folder_path)
        post_process_pdfs(folder_path,merged=True)


    else:
        post_process_pdfs(folder_path,merged=False)