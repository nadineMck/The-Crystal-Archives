import os
import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from tkinter import StringVar
from dotenv import load_dotenv
import re
import threading

# Load API key and validate
load_dotenv()
google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if not google_gemini_api_key:
    raise ValueError("Google Gemini API key not set. Check your .env file.")

# Global variable to store the anime name
anime_name = ""
myAnimeList_url = "https://myanimelist.net/"

# # Function to show and hide loading indicator
# def show_loading_indicator(label, text="Loading..."):
#     label.set(text)

# def hide_loading_indicator(label):
#     label.set("")

# Function to query Google Gemini API
def google_gemini_query(prompt):
    prompt = f"Using this website: {myAnimeList_url}, {prompt}"
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": google_gemini_api_key
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024  # Increased token limit
        }
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()
        result = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response content found.")
        return result
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return None

# Update on Line 48 and Line 52
def show_loading_indicator(indicator, button):
    # Schedule loading indicator to appear on the main thread
    def update_ui():
        indicator.pack(pady=5)  # Ensure visible
        indicator.start(10)  # Start spinning
        button.config(state=DISABLED)
        indicator.update_idletasks()  # Force UI update immediately

    root.after(0, update_ui)  # Ensure the UI update is scheduled


def hide_loading_indicator(indicator, button):
    indicator.stop()  # Stop spinning
    indicator.pack_forget()  # Hide the indicator
    button.config(state=NORMAL)
    # Ensure the UI updates immediately
    indicator.update_idletasks()
    
# Format text in the output widget
def format_text(text_widget, content):
    """Formats titles and highlights in the text widget."""
    text_widget.tag_configure("header", font=("Arial", 14, "bold"), foreground="#FFD700")
    text_widget.tag_configure("subheader", font=("Arial", 12, "italic"), foreground="#ADFF2F")
    text_widget.tag_configure("bold", font=("Arial", 12, "bold"), foreground="#FFFFFF")
    text_widget.tag_configure("bullet", font=("Arial", 12), foreground="#90EE90", lmargin1=20, lmargin2=40)
    text_widget.tag_configure("normal", font=("Arial", 12), wrap="word")

    # Parse and format the content
    bold_pattern = re.compile(r"\*\*(.*?)\*\*")
    bullet_pattern = re.compile(r"^\* (.*?)$")
    lines = content.splitlines()

    for line in lines:
        start = 0
        bullet_match = bullet_pattern.match(line)
        if bullet_match:
            text_widget.insert(ttk.END, bullet_match.group(1) + "\n", "bullet")
            continue
        for match in bold_pattern.finditer(line):
            start_index, end_index = match.span()
            # Insert normal text before bold text
            if start < start_index:
                text_widget.insert(ttk.END, line[start:start_index], "normal")
            # Insert bold text
            text_widget.insert(ttk.END, match.group(1), "bold")
            start = end_index
        # Insert any remaining normal text
        text_widget.insert(ttk.END, line[start:] + "\n", "normal")

# Generate a response
def generate_response(event=None):
    global anime_name
    anime_name = entry.get()
    if not anime_name:
        messagebox.showwarning("Input Error", "Please enter a prompt.")
        return

    def fetch_data():
        # Show loading indicator
        root.after(0, show_loading_indicator, loading_indicator, generate_button)

        # Perform the API call
        full_prompt = f"recommend me an anime to watch based on the following anime I liked: {anime_name}"
        result = google_gemini_query(full_prompt)

        # Hide loading indicator
        root.after(0, hide_loading_indicator, loading_indicator, generate_button)

        # Process the result
        if result:
            output_text.delete(1.0, ttk.END)  # Clear previous output
            format_text(output_text, result)  # Format and display the response
            details_button.config(state=NORMAL)  # Enable the details button
            details_output.delete(1.0, ttk.END)  # Clear details output
            details_entry.delete(0, ttk.END)  # Clear details entry


    threading.Thread(target=fetch_data).start()

def ask_for_details(event=None):
    if not anime_name:
        messagebox.showwarning("Input Error", "No anime name stored. Please generate a recommendation first.")
        return

    def fetch_details():
        # Show loading indicator
        root.after(0, show_loading_indicator, details_loading_indicator, details_generate_button)

        # Perform the API call
        detail_prompt = f"Recommend me an anime based on the following aspects I specifically liked in {anime_name} and this website: {myAnimeList_url}, and don't tell me to go to MAL website myself: {details_entry.get()}"
        result = google_gemini_query(detail_prompt)

        # Hide loading indicator
        root.after(0, hide_loading_indicator, details_loading_indicator, details_generate_button)

        # Process the result
        if result:
            details_output.delete(1.0, ttk.END)  # Clear previous output
            format_text(details_output, result)  # Format and display the response


    threading.Thread(target=fetch_details).start()
    
# Switch to the details screen
def switch_to_details():
    main_frame.pack_forget()
    details_frame.pack(fill=BOTH, expand=True)
    details_entry.focus()

# Switch back to the main screen
def switch_to_main():
    details_frame.pack_forget()
    main_frame.pack(fill=BOTH, expand=True)
    entry.focus()

# Create the main window
root = ttk.Window(themename="darkly")
root.title("Anime Recommender")
root.geometry("1000x720")

# Main screen
main_frame = ttk.Frame(root)
main_frame.pack(fill=BOTH, expand=True)

loading_label = ttk.Progressbar()
loading_indicator = ttk.Progressbar(main_frame, mode='indeterminate', style="info.Horizontal.TProgressbar")
# loading_indicator.pack(pady=5)

label = ttk.Label(main_frame, text="Which anime did you like?", font=("Arial", 12))
label.pack(pady=10)

entry = ttk.Entry(main_frame, width=50, font=("Arial", 12))
entry.pack(pady=10)
entry.bind('<Return>', generate_response)

generate_button = ttk.Button(main_frame, text="Generate Recommendation", command=generate_response, style="primary")
generate_button.pack(pady=5)

details_button = ttk.Button(main_frame, text="I specifically like the following aspects: ", command=switch_to_details, style="secondary", state=DISABLED)
details_button.pack(pady=5)

# Create a frame for the text and scrollbar
frame = ttk.Frame(main_frame)
frame.pack(pady=10, fill=BOTH, expand=True)

scrollbar = ttk.Scrollbar(frame, orient="vertical")
output_text = ttk.Text(frame, font=("Helvetica", 12), wrap=WORD, bg="#282C34", fg="#FFFFFF", yscrollcommand=scrollbar.set)
scrollbar.config(command=output_text.yview)

output_text.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.pack(side=RIGHT, fill=Y)

# Details screen
details_frame = ttk.Frame(root)

details_loading_label = ttk.Progressbar()
details_loading_indicator = ttk.Progressbar(details_frame, mode='indeterminate', style="info.Horizontal.TProgressbar")
# details_loading_indicator.pack(pady=5)

details_label = ttk.Label(details_frame, text="What specific aspects did you like?", font=("Arial", 12))
details_label.pack(pady=10)

details_entry = ttk.Entry(details_frame, width=50, font=("Arial", 12))
details_entry.pack(pady=10)
details_entry.bind('<Return>', ask_for_details)

back_button = ttk.Button(details_frame, text="Back", command=switch_to_main, style="danger")
back_button.pack(pady=5, anchor="w", padx=10)

# Generate button in details layer
details_generate_button = ttk.Button(details_frame, text="Generate Detailed Recommendation", command=ask_for_details, style="primary")
details_generate_button.pack(pady=5)

# Create a frame for the text and scrollbar in the details screen
details_output_frame = ttk.Frame(details_frame)
details_output_frame.pack(pady=10, fill=BOTH, expand=True)

details_scrollbar = ttk.Scrollbar(details_output_frame, orient="vertical")
details_output = ttk.Text(details_output_frame, font=("Helvetica", 12), wrap=WORD, bg="#282C34", fg="#FFFFFF", yscrollcommand=details_scrollbar.set)
details_scrollbar.config(command=details_output.yview)

details_output.pack(side=LEFT, fill=BOTH, expand=True)
details_scrollbar.pack(side=RIGHT, fill=Y)

# Run the GUI
root.mainloop()
