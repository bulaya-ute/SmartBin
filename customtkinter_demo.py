# customtkinter_demo.py

import customtkinter as ctk

ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

class DemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CustomTkinter Demo")
        self.geometry("400x300")

        # Main frame for layout
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Label
        self.label = ctk.CTkLabel(main_frame, text="Enter your name:")
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Entry
        self.entry = ctk.CTkEntry(main_frame, placeholder_text="Name")
        self.entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Button
        self.button = ctk.CTkButton(main_frame, text="Greet", command=self.greet)
        self.button.grid(row=1, column=0, columnspan=2, pady=10)

        # Checkbox
        self.checkbox = ctk.CTkCheckBox(main_frame, text="Subscribe to newsletter")
        self.checkbox.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        # Radio buttons
        self.radio_var = ctk.StringVar(value="Option 1")
        self.radio1 = ctk.CTkRadioButton(main_frame, text="Option 1", variable=self.radio_var, value="Option 1")
        self.radio2 = ctk.CTkRadioButton(main_frame, text="Option 2", variable=self.radio_var, value="Option 2")
        self.radio1.grid(row=3, column=0, pady=5, sticky="w")
        self.radio2.grid(row=3, column=1, pady=5, sticky="w")

        # Configure grid weights for resizing
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def greet(self):
        name = self.entry.get()
        self.label.configure(text=f"Hello, {name}!")

if __name__ == "__main__":
    app = DemoApp()
    app.mainloop()
