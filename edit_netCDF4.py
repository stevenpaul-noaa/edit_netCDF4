import netCDF4
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
# New import for autocomplete
from ttkwidgets.autocomplete import AutocompleteEntry

class NetCDFGlobalAttributeEditor:
    def __init__(self, master):
        self.master = master
        master.title("NetCDF Global Attribute Editor")
        master.geometry("600x500") # Set a default window size

        self.nc_file = None
        self.file_path = None
        self.global_attributes = {}

        # --- File Selection Frame ---
        self.file_frame = tk.Frame(master, padx=10, pady=10)
        self.file_frame.pack(fill=tk.X)

        self.file_label = tk.Label(self.file_frame, text="Selected File:")
        self.file_label.pack(side=tk.LEFT)

        self.file_path_display = tk.Entry(self.file_frame, width=50, state='readonly')
        self.file_path_display.pack(side=tk.LEFT, padx=5)

        self.select_file_button = tk.Button(self.file_frame, text="Select NetCDF File", command=self.select_netcdf_file)
        self.select_file_button.pack(side=tk.RIGHT)

        # --- Attributes Display Frame ---
        self.attr_frame = tk.LabelFrame(master, text="Global Attributes", padx=10, pady=10)
        self.attr_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.attr_text_area = scrolledtext.ScrolledText(self.attr_frame, wrap=tk.WORD, width=60, height=15)
        self.attr_text_area.pack(fill=tk.BOTH, expand=True)
        self.attr_text_area.config(state='disabled') # Make it read-only initially

        # --- Edit Attribute Frame ---
        self.edit_frame = tk.LabelFrame(master, text="Edit Attribute", padx=10, pady=10)
        self.edit_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(self.edit_frame, text="Attribute Name:").grid(row=0, column=0, sticky="w", pady=2)
        # Use AutocompleteEntry for the attribute name field
        self.attr_name_entry = AutocompleteEntry(self.edit_frame, width=40, completevalues=[])
        self.attr_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.attr_name_entry.bind("<Return>", self.get_current_value_from_entry) # Bind Enter key

        tk.Label(self.edit_frame, text="New Value:").grid(row=1, column=0, sticky="w", pady=2)
        self.new_value_entry = tk.Entry(self.edit_frame, width=40)
        self.new_value_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.new_value_entry.bind("<Return>", self.set_attribute_from_entry) # Bind Enter key

        self.get_value_button = tk.Button(self.edit_frame, text="Get Current Value", command=self.get_current_value)
        self.get_value_button.grid(row=0, column=2, padx=5)

        self.set_value_button = tk.Button(self.edit_frame, text="Set New Value", command=self.set_attribute)
        self.set_value_button.grid(row=1, column=2, padx=5)

        self.edit_frame.grid_columnconfigure(1, weight=1) # Allow entry to expand

        # --- Status Bar ---
        self.status_bar = tk.Label(master, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_netcdf_file(self):
        # Set the default directory here
        default_dir = r"A:\AVAPS\Data\Archive" # Use raw string (r"...") for backslashes

        # Check if the default directory exists, if not, open to current working directory
        if not os.path.isdir(default_dir):
            messagebox.showwarning(
                "Directory Not Found",
                f"Default directory '{default_dir}' does not exist. Opening to current working directory instead."
            )
            initial_directory = os.getcwd() # Fallback to current working directory
        else:
            initial_directory = default_dir

        file_path = filedialog.askopenfilename(
            title="Select NetCDF File",
            initialdir=initial_directory, # <-- This is where the default directory is used
            filetypes=[("NetCDF files", "*.nc *.netcdf *.cdf"), ("All files", "*.*")]
        )

        if not file_path:
            self.update_status("File selection cancelled.")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"The file '{file_path}' does not exist.")
            self.update_status("Error: File not found.")
            return
        if not file_path.lower().endswith(('.nc', '.netcdf', '.cdf')):
            messagebox.showwarning("Warning", "The selected file does not appear to be a NetCDF file (based on extension). Attempting to open anyway.")

        self.file_path = file_path
        self.file_path_display.config(state='normal')
        self.file_path_display.delete(0, tk.END)
        self.file_path_display.insert(0, self.file_path)
        self.file_path_display.config(state='readonly')
        
        self.open_netcdf_file()

    def open_netcdf_file(self):
        if self.nc_file:
            self.nc_file.close() # Close any previously opened file
            self.nc_file = None

        if not self.file_path:
            return

        try:
            self.nc_file = netCDF4.Dataset(self.file_path, 'r+')
            self.update_status(f"Successfully opened: {self.file_path}")
            self.load_global_attributes()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open NetCDF file: {e}\nPlease ensure it's a valid NetCDF file and you have write permissions.")
            self.update_status("Error opening file.")
            self.file_path = None
            self.file_path_display.config(state='normal')
            self.file_path_display.delete(0, tk.END)
            self.file_path_display.config(state='readonly')
            self.clear_attributes_display()
            # Clear autocomplete list if file opening fails
            self.attr_name_entry.set_completion_list([])

    def load_global_attributes(self):
        self.global_attributes = self.nc_file.__dict__
        self.clear_attributes_display()
        
        if not self.global_attributes:
            self.attr_text_area.config(state='normal')
            self.attr_text_area.insert(tk.END, "No global attributes found in this file.")
            self.attr_text_area.config(state='disabled')
            self.update_status("No global attributes found.")
            # Clear autocomplete list if no attributes
            self.attr_name_entry.set_completion_list([])
            return

        self.attr_text_area.config(state='normal')
        attr_str = ""
        for attr_name, attr_value in self.global_attributes.items():
            attr_str += f"- {attr_name}: {attr_value}\n"
        self.attr_text_area.insert(tk.END, attr_str)
        self.attr_text_area.config(state='disabled')
        self.update_status(f"Loaded {len(self.global_attributes)} global attributes.")

        # Update the autocomplete values for the attribute name entry
        self.attr_name_entry.set_completion_list(list(self.global_attributes.keys()))

    def clear_attributes_display(self):
        self.attr_text_area.config(state='normal')
        self.attr_text_area.delete(1.0, tk.END)
        self.attr_text_area.config(state='disabled')

    def get_current_value_from_entry(self, event=None):
        self.get_current_value()

    def get_current_value(self):
        attr_name = self.attr_name_entry.get().strip()
        if not attr_name:
            messagebox.showwarning("Input Error", "Please enter an attribute name.")
            self.update_status("No attribute name entered.")
            return

        if attr_name in self.global_attributes:
            current_value = self.global_attributes[attr_name]
            self.new_value_entry.delete(0, tk.END)
            self.new_value_entry.insert(0, str(current_value))
            self.update_status(f"Current value of '{attr_name}' loaded.")
        else:
            messagebox.showwarning("Attribute Not Found", f"Attribute '{attr_name}' not found.")
            self.update_status("Attribute not found.")

    def set_attribute_from_entry(self, event=None):
        self.set_attribute()

    def set_attribute(self):
        if not self.nc_file:
            messagebox.showerror("Error", "No NetCDF file is open.")
            self.update_status("No file open to edit.")
            return

        attr_name = self.attr_name_entry.get().strip()
        new_value_str = self.new_value_entry.get()

        if not attr_name:
            messagebox.showwarning("Input Error", "Please enter an attribute name to set.")
            self.update_status("No attribute name entered for setting.")
            return

        # Determine if the attribute exists or if it's a new one
        is_new_attribute = attr_name not in self.global_attributes

        if is_new_attribute:
            response = messagebox.askyesno(
                "Attribute Not Found",
                f"Attribute '{attr_name}' does not exist. Do you want to add it as a new attribute?"
            )
            if not response:
                self.update_status("User cancelled adding new attribute.")
                return

        # Determine the target type for the new value
        # If it's an existing attribute, try to keep its type.
        # If it's a new attribute, default to string, but try converting if possible.
        current_value_type = type(self.global_attributes.get(attr_name)) if not is_new_attribute else None # For new, we don't have a prior type

        try:
            new_value = new_value_str # Start assuming it's a string

            if current_value_type is int:
                new_value = int(new_value_str)
            elif current_value_type is float:
                new_value = float(new_value_str)
            elif is_new_attribute: # For new attributes, try to infer int/float if it parses cleanly
                try:
                    new_value = int(new_value_str)
                except ValueError:
                    try:
                        new_value = float(new_value_str)
                    except ValueError:
                        pass # Keep as string if not int or float

            setattr(self.nc_file, attr_name, new_value)
            self.global_attributes[attr_name] = new_value # Update local cache
            self.load_global_attributes() # Refresh display (this will also update autocomplete list)
            
            action_verb = "added" if is_new_attribute else "updated"
            self.update_status(f"Successfully {action_verb} '{attr_name}' to '{new_value}'.")
            messagebox.showinfo("Success", f"Successfully {action_verb} '{attr_name}' to '{new_value}'.")

        except ValueError:
            messagebox.showwarning(
                "Type Conversion Warning",
                f"Could not convert '{new_value_str}' to the original type of '{attr_name}' ({current_value_type.__name__ if current_value_type else 'string inferred'}). Storing as string."
            )
            setattr(self.nc_file, attr_name, new_value_str)
            self.global_attributes[attr_name] = new_value_str # Update local cache
            self.load_global_attributes() # Refresh display (this will also update autocomplete list)
            self.update_status(f"Stored '{attr_name}' as string: '{new_value_str}'.")

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while setting the attribute: {e}")
            self.update_status("Error setting attribute.")

    def update_status(self, message):
        self.status_bar.config(text=message)

    def on_closing(self):
        if self.nc_file:
            try:
                self.nc_file.close()
                self.update_status("NetCDF file closed.")
            except Exception as e:
                self.update_status(f"Error closing file: {e}")
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NetCDFGlobalAttributeEditor(root)
    # Handle window close event to ensure file is closed
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()