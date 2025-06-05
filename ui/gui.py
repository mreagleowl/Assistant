# ui/gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
import sounddevice as sd
import os
from core.transcriber import transcribe_audio
from core.email_sender import send_report_email
import datetime
import json

class VirtualSecretaryGUI:
    def __init__(self, config, gpt_summary_fn, recorder):
        self.config = config
        self.gpt_summary_fn = gpt_summary_fn
        self.recorder = recorder
        self.transcript_text = ""
        self.summary_text = ""
        self.email_selections = {}

        self.root = tk.Tk()
        self.root.title("Виртуальный Секретарь")
        self.root.geometry("920x750")

        # --- выпадающий список выбора промпта ---
        prompt_frame = tk.Frame(self.root)
        prompt_frame.pack(anchor="nw", padx=10, pady=(10,0))
        ttk.Label(prompt_frame, text="Тип выжимки:").grid(row=0, column=0, sticky="w")
        self.prompt_ids = list(self.config.get('prompts', {}).keys())
        self.prompt_var = tk.StringVar(value=self.prompt_ids[0] if self.prompt_ids else "")
        self.prompt_combo = ttk.Combobox(
            prompt_frame,
            textvariable=self.prompt_var,
            values=self.prompt_ids,
            state="readonly",
            width=40
        )
        self.prompt_combo.grid(row=0, column=1, padx=(5,0))

        # --- выбор микрофона ---
        self.device_blacklist = [b.lower() for b in self.config.get('audio', {}).get(
            'device_blacklist', ['virtual', 'stereo mix', 'loopback', 'cable']
        )]
        self.setup_device_selector()

        # --- основное текстовое поле ---
        self.text_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=25)
        self.text_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # --- панель кнопок ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Загрузить транскрипт", command=self.load_transcript).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Открыть аудио", command=self.load_audio_file).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Начать запись", command=self.start_recording).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Остановить и распознать", command=self.stop_recording).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Выжимка (GPT)", command=self.generate_summary).grid(row=0, column=4, padx=5)
        tk.Button(btn_frame, text="Сохранить отчёт", command=self.save_report).grid(row=0, column=5, padx=5)
        tk.Button(btn_frame, text="Отправить Email", command=self.open_recipient_selection).grid(row=0, column=6, padx=5)

    def setup_device_selector(self):
        df = tk.Frame(self.root)
        df.pack(anchor="nw", padx=10, pady=(10,0))
        ttk.Label(df, text="Микрофон:").grid(row=0, column=0, sticky="w")
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(df, textvariable=self.device_var,
                                         state="readonly", width=60)
        self.device_combo.grid(row=0, column=1, padx=(5,0))
        tk.Button(df, text="Обновить", command=self.refresh_devices).grid(row=0, column=2, padx=(5,0))
        self.refresh_devices()

    def refresh_devices(self):
        try:
            sd._terminate()
        except Exception:
            pass
        try:
            sd._initialize()
        except Exception:
            pass
        all_devices = sd.query_devices()
        opts = []
        for idx, dev in enumerate(all_devices):
            if dev.get('max_input_channels', 0) <= 0:
                continue
            name = dev.get('name', '')
            if any(bad in name.lower() for bad in self.device_blacklist):
                continue
            opts.append((idx, name))
        options = [f"{i} — {n}" for i, n in opts]
        self.device_combo['values'] = options
        if options:
            current = self.device_var.get()
            if current not in options:
                self.device_var.set(options[0])

    def run(self):
        self.root.mainloop()

    def load_transcript(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files","*.txt")])
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            self.transcript_text = f.read()
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.transcript_text)

    def load_audio_file(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files","*.wav"), ("All Files","*.*")])
        if not path:
            return
        try:
            self.transcript_text = transcribe_audio(path, self.config)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(tk.END, self.transcript_text)
            txt_path = os.path.splitext(path)[0] + ".txt"
            with open(txt_path, 'w', encoding='utf-8') as tf:
                tf.write(self.transcript_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обработать аудио: {e}")

    def start_recording(self):
        sel = self.device_var.get()
        if sel:
            idx = int(sel.split(" — ")[0])
            self.recorder.device = idx
        threading.Thread(target=self.recorder.start_recording).start()
        messagebox.showinfo("Запись","Запись началась.")

    def stop_recording(self):
        wav = self.recorder.stop_recording()
        self.transcript_text = transcribe_audio(wav, self.config)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.transcript_text)
        txt_path = os.path.splitext(wav)[0] + ".txt"
        try:
            with open(txt_path, 'w', encoding='utf-8') as tf:
                tf.write(self.transcript_text)
        except Exception as e:
            messagebox.showwarning("Сохранение транскрипта", f"Не удалось сохранить файл транскрипта: {e}")

    def generate_summary(self):
        if not self.transcript_text.strip():
            messagebox.showwarning("Нет текста","Загрузите сначала текст.")
            return
        # выбираем нужный промпт по идентификатору
        prompt_id = self.prompt_var.get()
        prompt_text = self.config.get('prompts', {}).get(prompt_id, None)
        self.summary_text = self.gpt_summary_fn(self.transcript_text, self.config, prompt_text)
        self.text_display.insert(tk.END, f"\n\n--- Выжимка ({prompt_id}) ---\n{self.summary_text}")

    def save_report(self):
        if not self.transcript_text:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"report_{ts}.txt")
        if not fp:
            return
        with open(fp,'w',encoding='utf-8') as f:
            f.write(self.transcript_text + "\n\n" + self.summary_text)
        messagebox.showinfo("Успех", f"Сохранено в {fp}")

    def open_recipient_selection(self):
        pass

    def send_email_selected(self, window):
        pass
