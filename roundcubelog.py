#import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import paramiko
import threading
import configparser
import os
from datetime import datetime
import re

class RoundcubeLogViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Roundcube Mail Log Viewer")
        self.root.geometry("900x600")
        
        # Create a config parser
        self.config = configparser.ConfigParser()
        self.config_file = os.path.expanduser("~/.roundcube_log_viewer.ini")
        
        # Load config if exists, otherwise use defaults
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['SERVER'] = {
                'hostname': 'your_server_hostname',
                'username': 'your_username',
                'port': '22',
                'use_key': 'True',
                'key_path': os.path.expanduser('~/.ssh/id_rsa'),
                'log_path': '/var/log/mail.log'
            }
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create search tab
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search Logs")
        
        # Create settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Set up the search tab
        self.setup_search_tab()
        
        # Set up the settings tab
        self.setup_settings_tab()
        
        # Configure tag colors for the text widget
        self.setup_text_tags()
        
        # Define keyword patterns to highlight
        self.setup_keyword_patterns()
    
    def setup_text_tags(self):
        # Configure text tags for coloring
        self.results_text.tag_configure("error", foreground="red")
        self.results_text.tag_configure("warning", foreground="orange")
        self.results_text.tag_configure("info", foreground="blue")
        self.results_text.tag_configure("header", foreground="green", font=("TkDefaultFont", 10, "bold"))
        self.results_text.tag_configure("success", foreground="green")
        self.results_text.tag_configure("highlight", background="yellow")
        
        # Additional tag colors for specific keywords
        self.results_text.tag_configure("clean_pass", foreground="green", background="#E0FFE0")  # Light green background
        self.results_text.tag_configure("reject", foreground="red", background="#FFE0E0")  # Light red background
        self.results_text.tag_configure("blocked", foreground="white", background="#AA0000")  # Dark red background
        self.results_text.tag_configure("milter_reject", foreground="white", background="#AA5500")  # Dark orange background
        self.results_text.tag_configure("unknown_user", foreground="white", background="#550000")  # Very dark red
    
    def setup_keyword_patterns(self):
        # Define patterns to match with their corresponding tags
        self.keyword_patterns = [
            (r"Passed CLEAN", "clean_pass"),
            (r"NOQUEUE reject", "reject"),
            (r"Blocked MTA-BLOCKED", "blocked"),
            (r"milter-reject", "milter_reject"),
            (r"User unknown in virtual mailbox table", "unknown_user")
        ]
    
    def setup_search_tab(self):
        # Email input field
        email_frame = ttk.Frame(self.search_frame)
        email_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(email_frame, text="Email Address:").pack(side='left')
        self.email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_var, width=40).pack(side='left', padx=5)
        
        # Additional parameters
        params_frame = ttk.Frame(self.search_frame)
        params_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(params_frame, text="Additional Parameters:").pack(side='left')
        self.params_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.params_var, width=40).pack(side='left', padx=5)
        
        # Search button
        btn_frame = ttk.Frame(self.search_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='left')
        
        self.search_btn = ttk.Button(btn_frame, text="Search Logs", command=self.search_logs)
        self.search_btn.pack(side='right')
        
        # Results area
        results_frame = ttk.LabelFrame(self.search_frame, text="Results")
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add a scrolled text widget for the results
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.results_text.config(state='disabled')
        
        # Add save button
        save_frame = ttk.Frame(self.search_frame)
        save_frame.pack(fill='x', padx=10, pady=10)
        
        self.save_btn = ttk.Button(save_frame, text="Save Results", command=self.save_results)
        self.save_btn.pack(side='right')
        self.save_btn.config(state='disabled')
    
    def setup_settings_tab(self):
        # Server settings
        server_frame = ttk.LabelFrame(self.settings_frame, text="Server Settings")
        server_frame.pack(fill='x', padx=10, pady=10)
        
        # Hostname
        hostname_frame = ttk.Frame(server_frame)
        hostname_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(hostname_frame, text="Hostname:").pack(side='left')
        self.hostname_var = tk.StringVar(value=self.config['SERVER']['hostname'])
        ttk.Entry(hostname_frame, textvariable=self.hostname_var, width=30).pack(side='left', padx=5)
        
        # Username
        username_frame = ttk.Frame(server_frame)
        username_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(username_frame, text="Username:").pack(side='left')
        self.username_var = tk.StringVar(value=self.config['SERVER']['username'])
        ttk.Entry(username_frame, textvariable=self.username_var, width=30).pack(side='left', padx=5)
        
        # Port
        port_frame = ttk.Frame(server_frame)
        port_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(port_frame, text="SSH Port:").pack(side='left')
        self.port_var = tk.StringVar(value=self.config['SERVER']['port'])
        ttk.Entry(port_frame, textvariable=self.port_var, width=10).pack(side='left', padx=5)
        
        # Authentication
        auth_frame = ttk.LabelFrame(self.settings_frame, text="Authentication")
        auth_frame.pack(fill='x', padx=10, pady=10)
        
        # Use SSH key or password
        self.use_key_var = tk.BooleanVar(value=self.config.getboolean('SERVER', 'use_key'))
        ttk.Checkbutton(auth_frame, text="Use SSH Key Authentication", variable=self.use_key_var, 
                        command=self.toggle_auth_method).pack(anchor='w', padx=5, pady=5)
        
        # SSH Key path
        self.key_frame = ttk.Frame(auth_frame)
        self.key_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(self.key_frame, text="SSH Key Path:").pack(side='left')
        self.key_path_var = tk.StringVar(value=self.config['SERVER']['key_path'])
        ttk.Entry(self.key_frame, textvariable=self.key_path_var, width=40).pack(side='left', padx=5)
        
        # Password field (hidden by default if using key auth)
        self.pass_frame = ttk.Frame(auth_frame)
        if not self.use_key_var.get():
            self.pass_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(self.pass_frame, text="Password:").pack(side='left')
        self.password_var = tk.StringVar()
        ttk.Entry(self.pass_frame, textvariable=self.password_var, show='*', width=30).pack(side='left', padx=5)
        
        # Log path
        log_frame = ttk.LabelFrame(self.settings_frame, text="Log Settings")
        log_frame.pack(fill='x', padx=10, pady=10)
        
        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(log_path_frame, text="Log File Path:").pack(side='left')
        self.log_path_var = tk.StringVar(value=self.config['SERVER']['log_path'])
        ttk.Entry(log_path_frame, textvariable=self.log_path_var, width=40).pack(side='left', padx=5)
        
        # Save settings button
        btn_frame = ttk.Frame(self.settings_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save Settings", command=self.save_settings).pack(side='right')
        ttk.Button(btn_frame, text="Test Connection", command=self.test_connection).pack(side='right', padx=10)
    
    def toggle_auth_method(self):
        if self.use_key_var.get():
            self.pass_frame.pack_forget()
            self.key_frame.pack(fill='x', padx=5, pady=5)
        else:
            self.key_frame.pack_forget()
            self.pass_frame.pack(fill='x', padx=5, pady=5)
    
    def save_settings(self):
        # Update config with current values
        self.config['SERVER']['hostname'] = self.hostname_var.get()
        self.config['SERVER']['username'] = self.username_var.get()
        self.config['SERVER']['port'] = self.port_var.get()
        self.config['SERVER']['use_key'] = str(self.use_key_var.get())
        self.config['SERVER']['key_path'] = self.key_path_var.get()
        self.config['SERVER']['log_path'] = self.log_path_var.get()
        
        # Write config to file
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
    
    def test_connection(self):
        # Create a new thread for testing connection
        threading.Thread(target=self._test_connection_thread, daemon=True).start()
    
    def _test_connection_thread(self):
        try:
            # Update status
            self.root.after(0, lambda: self.status_var.set("Testing connection..."))
            
            # Connect to the server
            ssh = self._connect_to_server()
            
            # Close connection
            ssh.close()
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo("Connection Test", "Successfully connected to the server!"))
            self.root.after(0, lambda: self.status_var.set("Ready"))
            
        except Exception as e:
            # Show error message
            self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Connection failed"))
    
    def _connect_to_server(self):
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Get connection details
        hostname = self.config['SERVER']['hostname']
        username = self.config['SERVER']['username']
        port = int(self.config['SERVER']['port'])
        use_key = self.config.getboolean('SERVER', 'use_key')
        
        # Connect using key or password
        if use_key:
            key_path = self.config['SERVER']['key_path']
            ssh.connect(hostname, port=port, username=username, key_filename=key_path)
        else:
            password = self.password_var.get()
            ssh.connect(hostname, port=port, username=username, password=password)
        
        return ssh
    
    def search_logs(self):
        # Validate email input
        email = self.email_var.get().strip()
        if not email:
            messagebox.showerror("Error", "Please enter an email address")
            return
        
        # Get additional parameters
        additional_params = self.params_var.get().strip()
        
        # Create a new thread for searching logs
        threading.Thread(target=self._search_logs_thread, 
                         args=(email, additional_params), 
                         daemon=True).start()
    
    def find_keyword_positions(self, line):
        """Find positions of all keywords in the line."""
        keyword_positions = []
        
        for pattern, tag in self.keyword_patterns:
            for match in re.finditer(pattern, line):
                keyword_positions.append((match.start(), match.end(), tag))
        
        return keyword_positions
    
    def apply_color_to_log_line(self, line):
        """Apply appropriate color tags to log lines based on content."""
        # Initialize tags list for this line
        base_tags = []
        
        # Convert to lowercase for case-insensitive matching
        lower_line = line.lower()
        
        # Find keyword positions for special highlighting
        keyword_positions = self.find_keyword_positions(line)
        
        # Add appropriate base tags based on content
        if "error" in lower_line or "failed" in lower_line or "failure" in lower_line:
            base_tags.append("error")
        elif "warning" in lower_line or "warn" in lower_line:
            base_tags.append("warning")
        elif "info" in lower_line or "notice" in lower_line:
            base_tags.append("info")
        elif "success" in lower_line or "completed" in lower_line:
            base_tags.append("success")
        
        # Find email position
        email = self.email_var.get().strip()
        email_pos = None
        if email in line:
            start_pos = line.find(email)
            end_pos = start_pos + len(email)
            email_pos = (start_pos, end_pos)
        
        return [(line, base_tags), email_pos, keyword_positions]
    
    def _search_logs_thread(self, email, additional_params):
        try:
            # Update UI
            self.root.after(0, lambda: self.status_var.set("Connecting to server..."))
            self.root.after(0, lambda: self.search_btn.config(state='disabled'))
            self.root.after(0, lambda: self.results_text.config(state='normal'))
            self.root.after(0, lambda: self.results_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.results_text.insert(tk.END, "Connecting to server...\n", "info"))
            self.root.after(0, lambda: self.results_text.config(state='disabled'))
            
            # Connect to the server
            ssh = self._connect_to_server()
            
            # Update status
            self.root.after(0, lambda: self.status_var.set("Searching logs..."))
            self.root.after(0, lambda: self.results_text.config(state='normal'))
            self.root.after(0, lambda: self.results_text.insert(tk.END, "Connected. Searching logs...\n\n", "success"))
            self.root.after(0, lambda: self.results_text.config(state='disabled'))
            
            # Build command
            log_path = self.config['SERVER']['log_path']
            command = f"cat {log_path} | grep \"{email}\""
            if additional_params:
                command += f" | grep \"{additional_params}\""
            
            # Execute command
            stdin, stdout, stderr = ssh.exec_command(command)
            
            # Get results
            results = stdout.read().decode('utf-8')
            errors = stderr.read().decode('utf-8')
            
            # Close connection
            ssh.close()
            
            # Display results
            self.root.after(0, lambda: self.results_text.config(state='normal'))
            
            if errors:
                self.root.after(0, lambda: self.results_text.insert(tk.END, "ERRORS:\n", "error"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, f"{errors}\n\n"))
            
            if results:
                self.root.after(0, lambda: self.results_text.insert(tk.END, "RESULTS:\n", "header"))
                
                # Process each line and apply appropriate coloring
                lines = results.splitlines()
                for i, line in enumerate(lines):
                    if line.strip():
                        colored_line, email_pos, keyword_positions = self.apply_color_to_log_line(line)
                        
                        # Insert the line with its base tags
                        line_text, base_tags = colored_line
                        position = self.results_text.index(tk.END)
                        self.root.after(0, lambda pos=position, txt=line_text+"\n", tgs=base_tags: 
                                       self.results_text.insert(pos, txt, tgs))
                        
                        # Get the line number for tag positions
                        line_number = int(float(position)) - 1
                        
                        # Apply email highlight tag if email was found
                        if email_pos:
                            start, end = email_pos
                            self.root.after(0, lambda ln=line_number, s=start, e=end: 
                                           self.results_text.tag_add("highlight", 
                                                                   f"{ln}.{s}", 
                                                                   f"{ln}.{e}"))
                        
                        # Apply keyword tags
                        for start, end, tag in keyword_positions:
                            self.root.after(0, lambda ln=line_number, s=start, e=end, t=tag: 
                                           self.results_text.tag_add(t, 
                                                                   f"{ln}.{s}", 
                                                                   f"{ln}.{e}"))
                
                self.root.after(0, lambda: self.save_btn.config(state='normal'))
            else:
                self.root.after(0, lambda: self.results_text.insert(tk.END, "No matching log entries found.", "info"))
                self.root.after(0, lambda: self.save_btn.config(state='disabled'))
            
            self.root.after(0, lambda: self.results_text.config(state='disabled'))
            self.root.after(0, lambda: self.status_var.set("Search completed"))
            self.root.after(0, lambda: self.search_btn.config(state='normal'))
            
        except Exception as e:
            # Show error message
            self.root.after(0, lambda: self.results_text.config(state='normal'))
            self.root.after(0, lambda: self.results_text.insert(tk.END, f"\nERROR: {str(e)}", "error"))
            self.root.after(0, lambda: self.results_text.config(state='disabled'))
            self.root.after(0, lambda: self.status_var.set("Error occurred"))
            self.root.after(0, lambda: self.search_btn.config(state='normal'))
    
    def save_results(self):
        # Get current results
        results = self.results_text.get(1.0, tk.END)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email = self.email_var.get().strip().replace('@', '_at_')
        filename = f"mail_logs_{email}_{timestamp}.txt"
        
        # Create file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=filename
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(results)
                messagebox.showinfo("Save Results", f"Results saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoundcubeLogViewer(root)
    root.mainloop()
