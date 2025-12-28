import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import io
import threading
import requests
import os
from datetime import datetime
from urllib.parse import quote
import random

# --- Configuration ---
# PASTE YOUR API KEY HERE
API_KEY = "PASTE YOUR API KEY HERE" 

print("--- Script Starting ---")
print(f"Using Pollinations.ai with Hardcoded API Key: {API_KEY[:5]}...")

class ImageGeneratorApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Pollinations.ai Image Generator (Multi-Model)")
        self.root.geometry("1080x600")

        # --- Style (Dark Theme) ---
        self.style = ttk.Style()
        try:
            available_themes = self.style.theme_names()
            if 'clam' in available_themes:
                self.style.theme_use('clam')
            elif 'alt' in available_themes:
                self.style.theme_use('alt')
        except tk.TclError:
            print("No suitable ttk theme found, using default.")

        # --- Define Dark Theme Colors ---
        BG_COLOR = "#2E2E2E"       
        FG_COLOR = "#EAEAEA"       
        SELECT_BG = "#4A4A4A"      
        SELECT_FG = "#FFFFFF"      
        BORDER_COLOR = "#3C3C3C"   
        ACCENT_COLOR = "#007ACC"   
        BUTTON_FG = "#FFFFFF"

        # --- Configure Root Window ---
        self.root.configure(bg=BG_COLOR)

        # --- Configure ttk Styles ---
        try:
            self.style.configure('.', background=BG_COLOR, foreground=FG_COLOR, fieldbackground=SELECT_BG,
                                 selectbackground=SELECT_BG, selectforeground=SELECT_FG, borderwidth=1, relief=tk.FLAT)
            self.style.map('.', background=[('active', SELECT_BG), ('disabled', BORDER_COLOR)],
                           foreground=[('disabled', BORDER_COLOR)])
            self.style.configure("TFrame", background=BG_COLOR)
            self.style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=('Calibri', 10))
            self.style.configure("TButton", background=ACCENT_COLOR, foreground=BUTTON_FG, font=('Helvetica', 10), borderwidth=0)
            self.style.map("TButton", background=[('active', '#005f9e')], foreground=[('disabled', BORDER_COLOR)])
            self.style.configure("Accent.TButton", font=('Helvetica', 10, 'bold'), background="#005f9e", foreground=BUTTON_FG)
            self.style.map("Accent.TButton", background=[('active', ACCENT_COLOR)])
            self.style.configure("TCombobox", fieldbackground=SELECT_BG, background=SELECT_BG, foreground=FG_COLOR,
                                 arrowcolor=FG_COLOR, bordercolor=BORDER_COLOR, lightcolor=BG_COLOR, darkcolor=BG_COLOR)
            self.style.map('TCombobox', fieldbackground=[('readonly', SELECT_BG)], selectbackground=[('readonly', SELECT_BG)],
                           selectforeground=[('readonly', SELECT_FG)])
            self.style.configure("TLabelframe", background=BG_COLOR, bordercolor=BORDER_COLOR, relief=tk.GROOVE)
            self.style.configure("TLabelframe.Label", background=BG_COLOR, foreground=ACCENT_COLOR, font=('Helvetica', 11, 'bold'))
        except tk.TclError as e:
            print(f"Warning: Could not apply all dark theme styles: {e}")

        self.pil_image = None 

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        main_frame.columnconfigure(0, weight=1) 
        main_frame.columnconfigure(1, weight=1) 
        main_frame.rowconfigure(1, weight=1) 

        # --- Input Controls Frame (Left Pane) ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.grid(row=0, column=0, rowspan=2, padx=(0, 10), pady=5, sticky="nsew")
        controls_frame.columnconfigure(0, weight=1)

        # 1. Model Selection (New)
        ttk.Label(controls_frame, text="Select Model:").grid(row=0, column=0, sticky="w", pady=(0,5))
        self.model_var = tk.StringVar(value="flux")
        models = ["flux", "z-image", "turbo"]
        self.model_combo = ttk.Combobox(controls_frame, textvariable=self.model_var, values=models, state="readonly", width=38)
        self.model_combo.grid(row=1, column=0, sticky="ew", pady=5)

        # 2. Prompt Input
        ttk.Label(controls_frame, text="Enter your prompt:").grid(row=2, column=0, sticky="w", pady=(10,5))
        self.prompt_text = scrolledtext.ScrolledText(
            controls_frame, wrap=tk.WORD, height=8, width=40, font=('Calibri', 12),
            background=SELECT_BG, foreground=FG_COLOR, insertbackground=FG_COLOR
        )
        self.prompt_text.grid(row=3, column=0, sticky="ew", pady=5)
        self.prompt_text.focus() 

        # 3. Aspect Ratio Selection
        ttk.Label(controls_frame, text="Select Aspect Ratio:").grid(row=4, column=0, sticky="w", pady=(10,5))
        self.aspect_ratio_var = tk.StringVar(value="1:1 (Square)")
        aspect_ratios = ["1:1 (Square)", "16:9 (Landscape)", "4:3 (Landscape)", "9:16 (Portrait)"]
        self.aspect_ratio_combo = ttk.Combobox(controls_frame, textvariable=self.aspect_ratio_var, values=aspect_ratios, state="readonly", width=38)
        self.aspect_ratio_combo.grid(row=5, column=0, sticky="ew", pady=5)
        
        # Generate Button
        self.generate_button = ttk.Button(controls_frame, text="Generate Image", command=self.start_generation_thread, style="Accent.TButton")
        self.generate_button.grid(row=7, column=0, sticky="ew", pady=(20,10), ipady=5)

        # Status Label
        self.status_label = ttk.Label(controls_frame, text="Ready.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.grid(row=8, column=0, sticky="sew", pady=(10,0), ipady=3)

        # --- Image Display Frame (Right Pane) ---
        image_display_frame = ttk.LabelFrame(main_frame, text="Generated Image", padding="10")
        image_display_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")
        image_display_frame.rowconfigure(0, weight=1)
        image_display_frame.columnconfigure(0, weight=1)

        self.image_label = ttk.Label(image_display_frame, anchor=tk.CENTER)
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Save Button
        self.save_button = ttk.Button(image_display_frame, text="Save Image Manually", command=self.manual_save_image, state=tk.DISABLED)
        self.save_button.grid(row=1, column=0, sticky="ew", pady=(10,0), ipady=3)
        
        self.status_label.config(text="Ready. Select Model and Enter Prompt.")

    def _get_dimensions_from_aspect_ratio(self, aspect_ratio_str):
        base_dim = 1024 
        ratio_map = {
            "1:1 (Square)": (base_dim, base_dim),
            "16:9 (Landscape)": (base_dim, int(base_dim * 9 / 16)),
            "4:3 (Landscape)": (base_dim, int(base_dim * 3 / 4)),
            "9:16 (Portrait)": (int(base_dim * 9 / 16), base_dim)
        }
        return ratio_map.get(aspect_ratio_str, (base_dim, base_dim))

    def start_generation_thread(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        selected_model = self.model_var.get()

        if not prompt:
            messagebox.showwarning("Input Error", "Please enter a prompt.")
            return
        
        # Check if API Key is set in the code
        if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY.strip():
            messagebox.showwarning("Configuration Error", "Please open the script and paste your API_KEY at line 14.")
            return

        aspect_ratio_str = self.aspect_ratio_var.get()
        width, height = self._get_dimensions_from_aspect_ratio(aspect_ratio_str)

        self.generate_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Generating with {selected_model}...")
        self.image_label.config(image='') 

        thread = threading.Thread(target=self.generate_image, args=(prompt, width, height, selected_model))
        thread.start()

    def generate_image(self, prompt, width, height, model_name):
        try:
            self.status_label.config(text=f"Requesting: {width}x{height} ({model_name})...")
            print(f"Generating with prompt: '{prompt}', W: {width}, H: {height}, Model: {model_name}")

            # --- Pollinations.ai API Call (Authenticated) ---
            base_url = "https://image.pollinations.ai/prompt/"
            encoded_prompt = quote(prompt)
            
            params = {
                "model": model_name,  # Uses selected model (flux, z-image, turbo)
                "width": width,
                "height": height,
                "seed": random.randint(0, 2**32 - 1),
                "nologo": "true",
                "private": "true", 
                "enhance": "true",
                "safe": "false" 
            }
            
            # Construct URL
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{base_url}{encoded_prompt}?{param_str}"
            
            # Auth Header
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Pollinations-Python-Client/1.0" 
            }

            print(f"Requesting URL: {url} with Auth Header")
            self.status_label.config(text="Sending Request to Pollinations...")

            http_response = requests.get(url, headers=headers, timeout=120) 
            
            if http_response.status_code == 401 or http_response.status_code == 403:
                raise requests.exceptions.HTTPError(f"Authentication Failed (Check API Key). Status: {http_response.status_code}")
                
            http_response.raise_for_status() 
            
            image_bytes = http_response.content
            print("Image data received successfully.")
            # --- End of API Call ---

            if image_bytes:
                self.pil_image = Image.open(io.BytesIO(image_bytes))
                
                self.auto_save_image(model_name) 

                max_display_width = self.image_label.winfo_width() - 20
                max_display_height = self.image_label.winfo_height() - 20
                if max_display_width < 50 or max_display_height < 50:
                    max_display_width = 400
                    max_display_height = 400

                img_for_display = self.pil_image.copy()
                img_for_display.thumbnail((max_display_width, max_display_height), Image.Resampling.LANCZOS)
                
                tk_image = ImageTk.PhotoImage(img_for_display)
                self.image_label.config(image=tk_image)
                self.image_label.image = tk_image
                
                self.status_label.config(text="Image generated and auto-saved!")
                self.save_button.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="Failed to obtain image bytes.")
                print("Image bytes were not obtained.")
                self.pil_image = None

        except requests.exceptions.HTTPError as e:
            error_text = f"HTTP Error: {e}"
            print(f"ERROR: {error_text}")
            self.status_label.config(text="Error encountered.")
            messagebox.showerror("API Error", f"{error_text}\n\nMake sure your API Key is correct and has credits.")
            self.pil_image = None
        except requests.exceptions.RequestException as e:
            error_text = f"Network Error: {e}"
            print(f"ERROR: {error_text}")
            self.status_label.config(text="Network Error.")
            messagebox.showerror("Network Error", error_text)
            self.pil_image = None
        except Exception as e:
            import traceback
            error_text = f"Unexpected error: {e}"
            print(f"ERROR: {error_text}\n{traceback.format_exc()}")
            self.status_label.config(text="Error.")
            messagebox.showerror("Generation Error", error_text)
            self.pil_image = None
        finally:
            if hasattr(self, 'generate_button'): self.generate_button.config(state=tk.NORMAL)

    def auto_save_image(self, model_name):
        if not self.pil_image:
            return
        outputs_dir = "Outputs"
        try:
            if not os.path.exists(outputs_dir):
                os.makedirs(outputs_dir)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            # Include model name in filename
            safe_model_name = model_name.replace("-", "")
            filename = f"{safe_model_name}_{timestamp}.png"
            filepath = os.path.join(outputs_dir, filename)
            self.pil_image.save(filepath, "PNG")
            print(f"Image auto-saved to {filepath}")
        except Exception as e:
            print(f"Error auto-saving image: {e}")

    def manual_save_image(self):
        if self.pil_image:
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
                    title="Save Image As",
                    initialdir="Outputs"
                )
                if file_path:
                    self.pil_image.save(file_path)
                    messagebox.showinfo("Success", f"Image saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
        else:
            messagebox.showwarning("No Image", "No image available to save.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    print("--- Script Ended ---")