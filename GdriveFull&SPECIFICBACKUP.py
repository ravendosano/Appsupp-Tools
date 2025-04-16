import os
import io
import threading
from datetime import datetime
from tkinter import Tk, Label, Entry, Button, StringVar, Frame, filedialog, Text, Scrollbar, VERTICAL, RIGHT, Y, END
from tkinter import ttk
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class DriveBackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Backup Tool")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # Variables
        self.service_account_path = StringVar()
        self.admin_email = StringVar()
        self.user_email = StringVar()
        self.backup_dir = StringVar()
        self.specific_file_names = StringVar()
        self.backup_status = "Ready"
        
        # Default values
        self.admin_email.set("jesson.estallo@ubiquity.com")
        self.backup_dir.set(os.path.expanduser("~/DriveBackups"))
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        # Create main frame
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Service account file
        Label(main_frame, text="Service Account JSON:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        Entry(main_frame, textvariable=self.service_account_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        Button(main_frame, text="Browse", command=self.browse_service_account).grid(row=0, column=2, padx=5, pady=5)
        
        # Admin email
        Label(main_frame, text="Admin Email:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        Entry(main_frame, textvariable=self.admin_email, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # User email
        Label(main_frame, text="User Email to Backup:", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        Entry(main_frame, textvariable=self.user_email, width=50).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Backup directory
        Label(main_frame, text="Backup Directory:", anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        Entry(main_frame, textvariable=self.backup_dir, width=50).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        Button(main_frame, text="Browse", command=self.browse_backup_dir).grid(row=3, column=2, padx=5, pady=5)
        
        # Specific file names input
        Label(main_frame, text="Specific File Names:", anchor="w").grid(row=4, column=0, sticky="w", pady=5)
        Entry(main_frame, textvariable=self.specific_file_names, width=50).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        Label(main_frame, text="(comma separated)", font=("Arial", 8)).grid(row=4, column=2, sticky="w", pady=5)
        
        # Button frame for multiple buttons
        button_frame = Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=15)
        
        # Start Backup button
        Button(button_frame, text="Start Full Backup", command=self.start_backup, bg="#4CAF50", fg="white", 
               height=2, width=15).pack(side="left", padx=10)
        
        # Download Specific Files button
        Button(button_frame, text="Download Specific Files", command=self.download_specific_files, bg="#2196F3", fg="white", 
               height=2, width=20).pack(side="left", padx=10)
        
        # Progress bar
        Label(main_frame, text="Progress:").grid(row=6, column=0, sticky="w", pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=6, column=1, columnspan=2, sticky="ew", pady=5)
        
        # Status label
        Label(main_frame, text="Status:").grid(row=7, column=0, sticky="nw", pady=5)
        
        # Log area with scrollbar
        log_frame = Frame(main_frame)
        log_frame.grid(row=7, column=1, columnspan=2, sticky="nsew", pady=5)
        
        scrollbar = Scrollbar(log_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.log_area = Text(log_frame, height=15, width=50, yscrollcommand=scrollbar.set)
        self.log_area.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_area.yview)
        
        # Configure grid weights for resizing
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(7, weight=1)
        
        # Initial log message
        self.log("Welcome to Google Drive Backup Tool")
        self.log("Please fill in all fields and click 'Start Backup'")
        self.log("Or enter specific file names (comma separated) and click 'Download Specific Files'")
    
    def browse_service_account(self):
        filename = filedialog.askopenfilename(
            title="Select Service Account JSON File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if filename:
            self.service_account_path.set(filename)
            self.log(f"Selected service account file: {filename}")
    
    def browse_backup_dir(self):
        directory = filedialog.askdirectory(title="Select Backup Directory")
        if directory:
            self.backup_dir.set(directory)
            self.log(f"Selected backup directory: {directory}")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(END, f"[{timestamp}] {message}\n")
        self.log_area.see(END)
        self.root.update_idletasks()
    
    def authenticate_service(self):
        """Authenticate and build the Drive API service."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path.get(), 
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Use domain-wide delegation to impersonate the user
            delegated_credentials = credentials.with_subject(self.user_email.get())
            
            # Build the Drive API service
            service = build('drive', 'v3', credentials=delegated_credentials)
            
            self.log(f"Successfully authenticated and impersonating user {self.user_email.get()}")
            return service
        
        except Exception as e:
            self.log(f"Authentication error: {str(e)}")
            return None
    
    def download_specific_files(self):
        """Download multiple specific files by name."""
        # Validate inputs
        if not self.service_account_path.get():
            self.log("Error: Service account JSON file is required")
            return
        
        if not self.user_email.get():
            self.log("Error: User email is required")
            return
            
        if not self.specific_file_names.get():
            self.log("Error: Please enter at least one file name to download")
            return
        
        # Disable buttons during operation
        self.disable_buttons()
        
        # Start download in a separate thread
        threading.Thread(target=self.run_specific_files_download, daemon=True).start()
    
    def run_specific_files_download(self):
        """Execute the specific files download process."""
        try:
            # Parse comma-separated file names, strip whitespace
            file_names = [name.strip() for name in self.specific_file_names.get().split(',') if name.strip()]
            
            self.log(f"Found {len(file_names)} file names to search for")
            
            if not file_names:
                self.log("No valid file names provided")
                return
            
            # Reset progress bar
            self.progress_bar["value"] = 0
            self.progress_bar["maximum"] = len(file_names)
            self.root.update_idletasks()
            
            # Authenticate
            service = self.authenticate_service()
            if not service:
                self.log("Authentication failed!")
                return
            
            # Prepare backup directory
            user_backup_dir = os.path.join(
                self.backup_dir.get(),
                f"{self.user_email.get().replace('@', '_at_')}",
                "specific_files"
            )
            os.makedirs(user_backup_dir, exist_ok=True)
            
            total_files_found = 0
            total_files_downloaded = 0
            
            # Process each file name
            for file_index, file_name in enumerate(file_names):
                self.log(f"Processing file name {file_index+1}/{len(file_names)}: {file_name}")
                
                # Update progress bar for each file name
                self.progress_bar["value"] = file_index + 1
                self.root.update_idletasks()
                
                # Search for the file by name
                query = f"name = '{file_name}'"
                
                files = []
                page_token = None
                
                while True:
                    response = service.files().list(
                        q=query,
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, parents)',
                        pageToken=page_token,
                        includeItemsFromAllDrives=True,
                        supportsAllDrives=True
                    ).execute()
                    
                    files.extend(response.get('files', []))
                    page_token = response.get('nextPageToken')
                    
                    if not page_token:
                        break
                
                if not files:
                    self.log(f"No files found with the name: {file_name}")
                    continue
                
                self.log(f"Found {len(files)} files with the name: {file_name}")
                total_files_found += len(files)
                
                # Process each found file
                all_files_dict = {}
                for i, file in enumerate(files):
                    file_id = file['id']
                    mime_type = file['mimeType']
                    
                    # Get parent folder information for path construction
                    all_parent_files = self.get_all_parent_files(service, file_id)
                    all_files_dict.update({f['id']: f for f in all_parent_files})
                    
                    # Determine file path based on parent folders
                    relative_path = self.get_file_path(file_id, file['name'], all_files_dict)
                    full_path = os.path.join(user_backup_dir, relative_path)
                    
                    # Create directory if needed
                    dir_path = os.path.dirname(full_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    self.log(f"Processing file instance {i+1}/{len(files)}: {relative_path}")
                    
                    # Handle different types of files
                    success = False
                    
                    # Handle Google Docs, Sheets, Slides, etc.
                    if mime_type == 'application/vnd.google-apps.document':
                        export_path = f"{full_path}.docx"
                        success = self.export_google_doc(service, file_id, 
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                export_path)
                    
                    elif mime_type == 'application/vnd.google-apps.spreadsheet':
                        export_path = f"{full_path}.xlsx"
                        success = self.export_google_doc(service, file_id, 
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                export_path)
                    
                    elif mime_type == 'application/vnd.google-apps.presentation':
                        export_path = f"{full_path}.pptx"
                        success = self.export_google_doc(service, file_id, 
                                'application/vnd.openxmlformats-officedocument.presentationml.presentation', 
                                export_path)
                    
                    elif mime_type == 'application/vnd.google-apps.drawing':
                        export_path = f"{full_path}.png"
                        success = self.export_google_doc(service, file_id, 'image/png', export_path)
                    
                    # Regular files
                    elif 'vnd.google-apps' not in mime_type:
                        success = self.download_file(service, file_id, full_path)
                    
                    else:
                        self.log(f"Skipping unsupported file type: {mime_type}")
                    
                    if success:
                        total_files_downloaded += 1
            
            self.log(f"Download completed! Found {total_files_found} files, successfully downloaded {total_files_downloaded}.")
            self.log(f"Files saved to: {user_backup_dir}")
            
        except Exception as e:
            self.log(f"Error during download: {str(e)}")
        
        finally:
            # Re-enable buttons
            self.enable_buttons()
    
    def get_all_parent_files(self, service, file_id):
        """Get all parent files needed for the path."""
        try:
            file_info = service.files().get(
                fileId=file_id, 
                fields='id, name, parents',
                supportsAllDrives=True
            ).execute()
            
            result = [file_info]
            
            # Get parents recursively
            if 'parents' in file_info:
                for parent_id in file_info['parents']:
                    parent_files = self.get_all_parent_files(service, parent_id)
                    result.extend(parent_files)
            
            return result
        except Exception as e:
            self.log(f"Error getting file info: {str(e)}")
            return []
    
    def start_backup(self):
        # Validate inputs
        if not self.service_account_path.get():
            self.log("Error: Service account JSON file is required")
            return
        
        if not self.user_email.get():
            self.log("Error: User email is required")
            return
        
        # Disable buttons during backup
        self.disable_buttons()
        
        # Start backup in a separate thread
        threading.Thread(target=self.run_backup, daemon=True).start()
    
    def disable_buttons(self):
        """Disable all buttons."""
        for widget in self.root.winfo_children():
            self.disable_buttons_in_widget(widget)
    
    def enable_buttons(self):
        """Enable all buttons."""
        for widget in self.root.winfo_children():
            self.enable_buttons_in_widget(widget)
    
    def disable_buttons_in_widget(self, widget):
        """Recursively disable buttons in a widget."""
        if isinstance(widget, Button):
            widget.config(state="disabled")
        elif hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self.disable_buttons_in_widget(child)
    
    def enable_buttons_in_widget(self, widget):
        """Recursively enable buttons in a widget."""
        if isinstance(widget, Button):
            widget.config(state="normal")
        elif hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self.enable_buttons_in_widget(child)
    
    def run_backup(self):
        try:
            self.log(f"Starting backup for user: {self.user_email.get()}")
            
            # Reset progress bar
            self.progress_bar["value"] = 0
            self.root.update_idletasks()
            
            # Prepare backup directory
            user_backup_dir = os.path.join(
                self.backup_dir.get(),
                f"{self.user_email.get().replace('@', '_at_')}",
                datetime.now().strftime("%Y-%m-%d")
            )
            os.makedirs(user_backup_dir, exist_ok=True)
            self.log(f"Backup directory: {user_backup_dir}")
            
            # Authenticate
            self.log("Authenticating...")
            service = self.authenticate_service()
            if not service:
                self.log("Authentication failed!")
                return
            
            # Get all files
            self.log("Fetching file list...")
            all_files = self.list_all_files(service)
            
            if not all_files:
                self.log("No files found to backup.")
                return
            
            file_count = len(all_files)
            self.log(f"Found {file_count} files to process.")
            
            # Create a dictionary of files for quick lookup
            files_dict = {file['id']: file for file in all_files}
            
            # Set up progress tracking
            self.progress_bar["maximum"] = file_count
            
            # Process each file
            success_count = 0
            for i, file in enumerate(all_files):
                file_id = file['id']
                file_name = file['name']
                mime_type = file['mimeType']
                
                # Update progress
                self.progress_bar["value"] = i + 1
                self.root.update_idletasks()
                
                # Determine file path based on parent folders
                relative_path = self.get_file_path(file_id, file_name, files_dict)
                full_path = os.path.join(user_backup_dir, relative_path)
                
                # Create directory if needed
                dir_path = os.path.dirname(full_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                
                self.log(f"Processing {i+1}/{file_count}: {relative_path}")
                
                # Handle different types of files
                success = False
                
                # Handle Google Docs, Sheets, Slides, etc.
                if mime_type == 'application/vnd.google-apps.document':
                    export_path = f"{full_path}.docx"
                    success = self.export_google_doc(service, file_id, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', export_path)
                
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    export_path = f"{full_path}.xlsx"
                    success = self.export_google_doc(service, file_id, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', export_path)
                
                elif mime_type == 'application/vnd.google-apps.presentation':
                    export_path = f"{full_path}.pptx"
                    success = self.export_google_doc(service, file_id, 'application/vnd.openxmlformats-officedocument.presentationml.presentation', export_path)
                
                elif mime_type == 'application/vnd.google-apps.drawing':
                    export_path = f"{full_path}.png"
                    success = self.export_google_doc(service, file_id, 'image/png', export_path)
                
                elif mime_type == 'application/vnd.google-apps.folder':
                    # Just create the folder
                    os.makedirs(full_path, exist_ok=True)
                    success = True
                    self.log(f"Created folder: {relative_path}")
                
                # Regular files
                elif 'vnd.google-apps' not in mime_type:
                    success = self.download_file(service, file_id, full_path)
                
                else:
                    self.log(f"Skipping unsupported file type: {mime_type}")
                
                if success:
                    success_count += 1
            
            # Backup completed
            self.log(f"\nBackup complete! Successfully processed {success_count} out of {file_count} files.")
            self.log(f"Backup location: {user_backup_dir}")
            
        except Exception as e:
            self.log(f"Error during backup: {str(e)}")
        
        finally:
            # Re-enable buttons
            self.enable_buttons()
    
    def list_all_files(self, service):
        """List all files in the user's Drive."""
        all_files = []
        page_token = None
        
        try:
            while True:
                results = service.files().list(
                    pageSize=1000,
                    fields="nextPageToken, files(id, name, mimeType, parents)",
                    pageToken=page_token,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True
                ).execute()
                
                items = results.get('files', [])
                all_files.extend(items)
                
                self.log(f"Retrieved {len(all_files)} files so far...")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            return all_files
        
        except Exception as e:
            self.log(f"Error listing files: {str(e)}")
            return []
    
    def get_file_path(self, file_id, file_name, files_dict, path_cache=None):
        """Determine the file path based on parent folders."""
        if path_cache is None:
            path_cache = {}
        
        if file_id in path_cache:
            return path_cache[file_id]
        
        file_info = files_dict.get(file_id)
        if not file_info:
            return file_name
        
        # Get parent IDs
        parents = file_info.get('parents', [])
        
        if not parents:
            path = file_name
        else:
            parent_id = parents[0]  # Take the first parent
            parent_info = files_dict.get(parent_id)
            
            if not parent_info:
                path = file_name
            else:
                parent_path = self.get_file_path(parent_id, parent_info['name'], files_dict, path_cache)
                path = os.path.join(parent_path, file_name)
        
        path_cache[file_id] = path
        return path
    
    def download_file(self, service, file_id, file_path):
        """Download a file from Drive."""
        try:
            request = service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(file_stream.getvalue())
            
            self.log(f"Downloaded file successfully")
            return True
        except Exception as e:
            self.log(f"Error downloading file: {str(e)}")
            return False
    
    def export_google_doc(self, service, file_id, mime_type, file_path):
        """Export a Google Document to the specified MIME type."""
        try:
            request = service.files().export_media(fileId=file_id, mimeType=mime_type)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(file_stream.getvalue())
            
            self.log(f"Exported file successfully")
            return True
        except Exception as e:
            self.log(f"Error exporting file: {str(e)}")
            return False

if __name__ == "__main__":
    root = Tk()
    app = DriveBackupApp(root)
    root.mainloop()