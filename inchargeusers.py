import tkinter as tk
from tkinter import messagebox
import requests

# Function to fetch all user data from the API
def fetch_all_users():
    api_url = "https://incharge.ubiquity.com/api/user/"
    try:
        # Make a GET request to the API
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            messagebox.showerror("Error", f"Failed to fetch data. Status Code: {response.status_code}")
            return []
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return []

# Function to search for the user based on the username
def search_user():
    username = entry.get()
    
    # Check if the input is empty
    if not username.strip():
        messagebox.showwarning("Input Error", "Please enter a username to search.")
        return

    # Search for the user in the previously fetched list of users
    matching_users = [user for user in users if username.lower() in user['username'].lower()]
    
    if matching_users:
        # Show the first match (you can modify this if you want to show all matches)
        user = matching_users[0]
        
        # Create a tabulated output with labels
        user_info = (
            f"{'Field':<25}{'Value'}\n"
            f"{'-'*50}\n"
            f"{'ID:':<25}{user['id']}\n"
            f"{'Username:':<25}{user['username']}\n"
            f"{'Name:':<25}{user['first_name']} {user['last_name']}\n"
            f"{'Email:':<25}{user['email']}\n"
            f"{'Role:':<25}{user['profile']['user_role']['display_name'] if user.get('profile') else 'N/A'}\n"
            f"{'Active:':<25}{'Yes' if user['is_active'] else 'No'}\n"
            f"{'Reports To:':<25}{user['profile']['reports_to_user'] if user['profile']['reports_to_user'] else 'None'}\n"
            f"{'User Programs:':<25}{', '.join([prog['name'] for prog in user['profile']['user_programs']])}\n"
            f"{'Profile Department:':<25}{user['profile']['department'] if user.get('profile') else 'N/A'}\n"
            f"{'Password:':<25}{user['password']}\n"
        )
        
        # Display the information in a formatted way
        result_text.delete(1.0, tk.END)  # Clear previous content
        result_text.insert(tk.END, user_info)
    else:
        messagebox.showinfo("No Matches", "No user found with that username.")

# Initialize the users data
users = fetch_all_users()

# Set up the Tkinter window
root = tk.Tk()
root.title("User Info Fetcher")

# Create and place the UI components
label = tk.Label(root, text="Enter Username:")
label.pack(padx=20, pady=10)

entry = tk.Entry(root)
entry.pack(padx=20, pady=5)

search_button = tk.Button(root, text="Search User", command=search_user)
search_button.pack(pady=20)

# Create a Text widget to display the user info in tabular format
result_text = tk.Text(root, height=15, width=70, wrap=tk.WORD, font=("Courier", 10))
result_text.pack(padx=20, pady=10)

# Run the Tkinter event loop
root.mainloop()
