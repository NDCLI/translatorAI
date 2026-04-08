import customtkinter as ctk
from translator_engine import TranslatorEngine
import pyperclip
import threading
import keyboard
from history_manager import HistoryManager

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Translator")
        self.geometry("900x600")

        self.translator = TranslatorEngine()
        self.translate_timer = None
        self.current_request_id = 0
        self.history_manager = HistoryManager()

        # self.setup_hotkeys()

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header Section ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")

        langs = self.translator.get_supported_languages()
        
        self.source_lang_combo = ctk.CTkComboBox(self.header_frame, values=langs, width=180)
        self.source_lang_combo.set("Auto Detect")
        self.source_lang_combo.pack(side="left", padx=10)

        self.swap_btn = ctk.CTkButton(self.header_frame, text="⇄", width=40, font=("Arial", 20), 
                                      command=self.swap_languages)
        self.swap_btn.pack(side="left", padx=5)

        self.target_lang_combo = ctk.CTkComboBox(self.header_frame, values=langs, width=180)
        self.target_lang_combo.set("Vietnamese")
        self.target_lang_combo.pack(side="left", padx=10)

        # Switch to toggle always on top
        self.always_on_top_var = ctk.BooleanVar(value=False)
        self.always_on_top_switch = ctk.CTkSwitch(self.header_frame, text="Ghim cửa sổ (Always on top)", 
                                                  command=self.toggle_always_on_top,
                                                  variable=self.always_on_top_var,
                                                  font=("Inter", 13, "bold"),
                                                  button_color="#4CAF50",
                                                  progress_color="#45a049")
        self.always_on_top_switch.pack(side="right", padx=20)

        # --- Body Section ---
        # Input Text
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")
        
        self.input_label = ctk.CTkLabel(self.input_frame, text="Văn bản nguồn", font=("Inter", 14, "bold"))
        self.input_label.pack(pady=5)
        
        self.input_text = ctk.CTkTextbox(self.input_frame, font=("Inter", 14), undo=True)
        self.input_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.input_text.bind("<KeyRelease>", self.on_input_change)

        # Output Text
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")
        
        self.output_label = ctk.CTkLabel(self.output_frame, text="Bản dịch", font=("Inter", 14, "bold"))
        self.output_label.pack(pady=5)
        
        self.output_text = ctk.CTkTextbox(self.output_frame, font=("Inter", 14), fg_color="#2b2b2b")
        self.output_text.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Footer Section ---
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self.copy_btn = ctk.CTkButton(self.footer_frame, text="Sao chép kết quả", height=45, fg_color="#333333", 
                                      hover_color="#444444", command=self.copy_result)
        self.copy_btn.pack(side="right", padx=10)

        self.history_btn = ctk.CTkButton(self.footer_frame, text="Lịch sử", height=45, width=100,
                                         fg_color="transparent", border_width=1, border_color="#555555",
                                         command=self.show_history_window)
        self.history_btn.pack(side="left", padx=10)

        self.status_label = ctk.CTkLabel(self, text="Sẵn sàng", font=("Inter", 12))
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(0, 0))

        self.progress_bar = ctk.CTkProgressBar(self, height=2, corner_radius=0)
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")

    def setup_hotkeys(self):
        # Register global hotkey
        try:
            keyboard.add_hotkey('ctrl+alt+t', self.on_hotkey_pressed)
        except Exception as e:
            print(f"Hotkey error: {e}")

    def on_hotkey_pressed(self):
        # Trigger when Ctrl+Alt+T is pressed
        clip_text = pyperclip.paste().strip()
        if clip_text:
            self.after(0, lambda: self.process_clipboard_text(clip_text))

    def process_clipboard_text(self, text):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)
        self.deiconify() # Show window
        self.focus_force() # Focus window
        self.attributes("-topmost", True) # Temp on top
        if not self.always_on_top_var.get():
            self.after(1000, lambda: self.attributes("-topmost", False))
        self.perform_translation()

    def toggle_always_on_top(self):
        is_on_top = self.always_on_top_var.get()
        self.attributes("-topmost", is_on_top)
        msg = "Đã ghim: Cửa sổ sẽ luôn hiển thị bên trên các ứng dụng khác." if is_on_top else "Đã bỏ ghim cửa sổ."
        self.set_status(msg)

    def on_input_change(self, event=None):
        text = self.input_text.get("1.0", "end-1c").strip()
        
        if not text:
            self.output_text.delete("1.0", "end")
            self.set_status("Sẵn sàng")
            if self.translate_timer is not None:
                self.after_cancel(self.translate_timer)
            self.source_lang_combo.set("Auto Detect")
            return

        if self.translate_timer is not None:
            self.after_cancel(self.translate_timer)
            
        self.translate_timer = self.after(800, self.perform_translation)

    def swap_languages(self):
        s = self.source_lang_combo.get()
        t = self.target_lang_combo.get()
        if s == "Auto Detect": return 
        self.source_lang_combo.set(t)
        self.target_lang_combo.set(s)
        
        input_content = self.input_text.get("1.0", "end-1c")
        output_content = self.output_text.get("1.0", "end-1c")
        
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        
        if output_content: self.input_text.insert("1.0", output_content)
        if input_content: self.output_text.insert("1.0", input_content)

    def set_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def perform_translation(self):
        text = self.input_text.get("1.0", "end-1c").strip()
        if not text:
            return

        src = self.source_lang_combo.get()
        dest = self.target_lang_combo.get()
        
        if src == "Auto Detect":
            detected = self.translator.detect_language(text)
            if detected != "Auto Detect":
                # Smart Swap: If detected language is same as target, swap target
                if detected == dest:
                    new_dest = "English" if detected == "Vietnamese" else "Vietnamese"
                    self.after(0, lambda: self.target_lang_combo.set(new_dest))
                    dest = new_dest
                
                self.after(0, lambda d=detected: self.source_lang_combo.set(d))
                src = detected

        self.set_status("Đang dịch...")
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        self.current_request_id += 1
        req_id = self.current_request_id

        def _task(rid):
            res = self.translator.translate(text, src, dest)
            self.after(0, lambda: self.show_result(res, rid))
        
        threading.Thread(target=_task, args=(req_id,), daemon=True).start()

    def show_result(self, result, rid):
        if rid != self.current_request_id:
            return
            
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.set_status("Đã dịch xong.")
        
        # Save to history
        src_text = self.input_text.get("1.0", "end-1c").strip()
        src_lang = self.source_lang_combo.get()
        dest_lang = self.target_lang_combo.get()
        if src_text and result:
            self.history_manager.add_entry(src_text, result, src_lang, dest_lang)

    def show_history_window(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Lịch sử bản dịch")
        history_window.geometry("600x500")
        history_window.after(10, history_window.focus_force)
        history_window.attributes("-topmost", True)

        label = ctk.CTkLabel(history_window, text="Các bản dịch gần đây", font=("Inter", 16, "bold"))
        label.pack(pady=10)

        scrollable_frame = ctk.CTkScrollableFrame(history_window, width=550, height=380)
        scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        history_data = self.history_manager.get_history()
        
        if not history_data:
            ctk.CTkLabel(scrollable_frame, text="Chưa có dữ liệu lịch sử.").pack(pady=20)
        
        for entry in history_data:
            frame = ctk.CTkFrame(scrollable_frame, fg_color="#2b2b2b")
            frame.pack(fill="x", pady=5, padx=5)
            
            # Header with language and time
            header_text = f"[{entry['timestamp']}] {entry['src_lang']} ➔ {entry['dest_lang']}"
            ctk.CTkLabel(frame, text=header_text, font=("Inter", 11, "italic"), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(5, 0))
            
            # Source text
            src_lbl = ctk.CTkLabel(frame, text=entry['source'], font=("Inter", 13), wraplength=500, justify="left")
            src_lbl.pack(anchor="w", padx=10, pady=2)
            
            # Divider
            ctk.CTkFrame(frame, height=1, fg_color="#444444").pack(fill="x", padx=10)
            
            # Target text
            dest_lbl = ctk.CTkLabel(frame, text=entry['target'], font=("Inter", 13, "bold"), 
                                    text_color="#4CAF50", wraplength=500, justify="left")
            dest_lbl.pack(anchor="w", padx=10, pady=(2, 5))
            
            # Click to restore button (optional, but good)
            restore_btn = ctk.CTkButton(frame, text="Khôi phục", height=20, width=80, font=("Inter", 10),
                                        fg_color="#333333", command=lambda e=entry: self.restore_history(e, history_window))
            restore_btn.pack(side="right", padx=10, pady=(0, 5))

    def restore_history(self, entry, window):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", entry['source'])
        self.source_lang_combo.set(entry['src_lang'])
        self.target_lang_combo.set(entry['dest_lang'])
        self.perform_translation()
        window.destroy()

    def copy_result(self):
        res = self.output_text.get("1.0", "end-1c")
        if res:
            pyperclip.copy(res)
            self.set_status("Đã sao chép vào bộ nhớ tạm.")

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            import traceback
            f.write(str(e))
            f.write("\n")
            f.write(traceback.format_exc())
