import tkinter as tk
from tkinter import filedialog, scrolledtext
from pypdf import PdfReader, PdfWriter
from collections import Counter
import os
import sys
import ctypes

# =========================
# RESOURCE PATH + ДИАГНОСТИКА
# =========================
def resource_path(relative_path):
    """Универсальная функция поиска ресурсов: работает в dev-режиме и в EXE"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    full_path = os.path.join(base_path, relative_path)
    print(f"[DEBUG] Resource requested: {relative_path} → {full_path}")
    return full_path


# =========================
# ИКОНКИ
# =========================
def setup_window_icon(root):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.pdfconverter.gui.1.0')
    except:
        pass

    png_path = resource_path("icon.png")
    if os.path.exists(png_path):
        try:
            icon_img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, icon_img)
            root._icon_img = icon_img
            print(f"✅ Иконка PNG загружена: {png_path}")
            return
        except Exception as e:
            print(f"❌ Ошибка загрузки PNG: {e}")

    ico_path = resource_path("icon.ico")
    if os.path.exists(ico_path):
        try:
            root.iconbitmap(ico_path)
            print(f"✅ Иконка ICO загружена: {ico_path}")
        except Exception as e:
            print(f"❌ Ошибка загрузки ICO: {e}")
    else:
        print("⚠️ Ни icon.png, ни icon.ico не найдены!")


# =========================
# РАБОТА С PDF И ЛОГИКА
# =========================
def log_block(box, title, content, status):
    box.configure(state="normal")
    box.insert(tk.END, "—" * 60 + "\n")
    box.insert(tk.END, f"[{status.upper()}] {title}\n\n")
    box.insert(tk.END, content + "\n\n")
    box.see(tk.END)
    box.configure(state="disabled")


def ratio_class(w, h):
    r = w / h
    if abs(r - 1.414) < 0.03: return "A-series"
    if abs(r - 1.333) < 0.03: return "4:3"
    if abs(r - 1.777) < 0.03: return "16:9"
    if abs(r - 0.75) < 0.03:  return "3:4"
    if abs(r - 0.666) < 0.03: return "2:3"
    return f"custom ({w:.2f}:{h:.2f})"


def analyze_pdf(path, box):
    reader = PdfReader(path)
    ratios = []
    file_name = os.path.basename(path)

    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        ratios.append(ratio_class(w, h))

    counter = Counter(ratios)
    content = "Unique aspect ratios found:\n"
    for k, v in counter.items():
        content += f"  • {k}: {v} pages\n"

    log_block(box, f"ANALYZE: {file_name}", content, "info")


def resize_pdf_pure_python(input_path, output_path, w_ratio, h_ratio, box):
    file_name = os.path.basename(input_path)
    
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        target_width = 595.0
        target_height = target_width * h_ratio / w_ratio

        for original_page in reader.pages:
            current_width = float(original_page.mediabox.width)
            current_height = float(original_page.mediabox.height)

            fit_x = target_width / current_width
            fit_y = target_height / current_height
            scale = min(fit_x, fit_y)

            new_content_w = current_width * scale
            new_content_h = current_height * scale

            offset_x = (target_width - new_content_w) / 2
            offset_y = (target_height - new_content_h) / 2

            page = writer.add_page(original_page)
            page.scale(scale, scale)
            
            page.mediabox.left = -offset_x
            page.mediabox.bottom = -offset_y
            page.mediabox.right = target_width - offset_x
            page.mediabox.top = target_height - offset_y

            page.cropbox.left = page.mediabox.left
            page.cropbox.bottom = page.mediabox.bottom
            page.cropbox.right = page.mediabox.right
            page.cropbox.top = page.mediabox.top
            
            if hasattr(page, 'bleedbox'): page.bleedbox = page.mediabox
            if hasattr(page, 'trimbox'):  page.trimbox = page.mediabox
            if hasattr(page, 'artbox'):   page.artbox = page.mediabox

            page.compress_content_streams()

        with open(output_path, "wb") as f:
            writer.write(f)
            
        status = "success"
        content = f"Target grid: {target_width:.0f} x {target_height:.0f} points.\nAll pages adjusted seamlessly with borders."
    except Exception as e:
        status = "error"
        content = str(e)

    log_block(box, f"RESIZE: {file_name}", content, status)


# =========================
# КАСТОМНЫЕ СТИЛЬНЫЕ ВИДЖЕТЫ
# =========================
class ModernButton(tk.Button):
    """Плоская светлая кнопка со сглаженными реакциями на мышь"""
    def __init__(self, master, kw=None, **kwargs):
        bg = kwargs.pop('bg', '#EAEAEA')
        fg = kwargs.pop('fg', '#1A1A1A')
        activebg = kwargs.pop('activebackground', '#DCDCDC')
        activefg = kwargs.pop('activeforeground', '#000000')
        
        super().__init__(master, bg=bg, fg=fg, activebackground=activebg, 
                         activeforeground=activefg, bd=0, relief="flat", 
                         cursor="hand2", overrelief="flat", **kwargs)
        
        self.default_bg = bg
        self.hover_bg = activebg
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['bg'] = self.hover_bg

    def on_leave(self, e):
        self['bg'] = self.default_bg


# =========================
# GUI (КРУПНЫЙ СВЕТЛЫЙ ИНТЕРФЕЙС)
# =========================
class App:
    def __init__(self, root):
        self.root = root
        self.input_path = None

        # Палитра UI (Светлая тема)
        self.bg_color = "#F9F9FB"       # Мягкий белый фон
        self.card_color = "#FFFFFF"     # Чисто белый цвет для карточек
        self.border_color = "#E5E5EA"   # Светло-серый разделитель
        self.accent_color = "#0066CC"   # Насыщенный синий (Apple Style)
        self.text_color = "#3A3A3C"     # Темно-серый текст (вместо едкого черного)
        
        # УВЕЛИЧЕННЫЕ ШРИФТЫ
        font_title = ("Segoe UI", 22, "bold")
        font_subtitle = ("Segoe UI", 14)
        font_label = ("Segoe UI", 14, "bold")
        font_input = ("Segoe UI", 15)   # Крупный текст в инпутах
        font_btn = ("Segoe UI", 16, "bold") # Заметный текст на кнопках

        # Главный контейнер
        main_frame = tk.Frame(root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=40, pady=35)


        # Крупная кнопка выбора файла
        self.btn_open = ModernButton(main_frame, text="📂   Select source PDF", font=font_btn, 
                                     bg="#F2F2F7", fg="#1C1C1E", activebackground="#E5E5EA",
                                     height=2)
        self.btn_open.pack(fill="x", pady=(0, 20))
        self.btn_open.configure(command=self.open_pdf)

        # Блок настроек пропорций (Белая объемная карточка)
        settings_card = tk.Frame(main_frame, bg=self.card_color, bd=1, relief="solid", highlightthickness=0, colormap="")
        # Имитируем тонкую рамку вокруг карточки
        settings_card.configure(highlightbackground=self.border_color, highlightcolor=self.border_color, highlightthickness=1, bd=0)
        settings_card.pack(fill="x", pady=(0, 20), ipady=15)

        # Контейнер полей ввода внутри карточки
        grid_input = tk.Frame(settings_card, bg=self.card_color)
        grid_input.pack(pady=15)

        # Поле ширины (Крупное)
        tk.Label(grid_input, text="Width ratio", font=font_label, bg=self.card_color, fg=self.text_color).grid(row=0, column=0, padx=20, sticky="w")
        self.w_entry = tk.Entry(grid_input, width=10, font=font_input, bg="#F2F2F7", fg="#000000", bd=0, insertbackground="black", justify="center")
        self.w_entry.grid(row=1, column=0, padx=20, pady=(8, 0), ipady=10) # Увеличена внутренняя высота (ipady)
        self.add_inner_style(self.w_entry)

        # Разделитель X
        tk.Label(grid_input, text="✕", font=("Segoe UI", 14), bg=self.card_color, fg="#AEAEB2").grid(row=1, column=1, pady=(8, 0))

        # Поле высоты (Крупное)
        tk.Label(grid_input, text="Height ratio", font=font_label, bg=self.card_color, fg=self.text_color).grid(row=0, column=2, padx=20, sticky="w")
        self.h_entry = tk.Entry(grid_input, width=10, font=font_input, bg="#F2F2F7", fg="#000000", bd=0, insertbackground="black", justify="center")
        self.h_entry.grid(row=1, column=2, padx=20, pady=(8, 0), ipady=10)
        self.add_inner_style(self.h_entry)

        # Блок основных действий
        actions_frame = tk.Frame(main_frame, bg=self.bg_color)
        actions_frame.pack(fill="x", pady=(0, 25))

        self.btn_analyze = ModernButton(actions_frame, text="📊   Analyze", font=font_btn, bg="#E5E5EA", fg="#1C1C1E", activebackground="#D1D1D6")
        self.btn_analyze.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=12) # Увеличена высота кнопок
        self.btn_analyze.configure(command=self.analyze)

        self.btn_resize = ModernButton(actions_frame, text="📐   Generate PDF", font=font_btn, bg=self.accent_color, fg="#FFFFFF", activebackground="#0055B3")
        self.btn_resize.pack(side="right", fill="x", expand=True, padx=(10, 0), ipady=12)
        self.btn_resize.configure(command=self.resize)

        # Консоль / Вывод логов (Светлый чистый терминал)
        tk.Label(main_frame, text="Process Logs", font=font_label, bg=self.bg_color, fg="#8E8E93").pack(anchor="w", pady=(0, 8))
        self.out = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=("Consolas", 12),
                                             bg="#FFFFFF", fg="#2C2C2E", bd=0, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.accent_color)
        self.out.pack(expand=True, fill="both")
        self.out.configure(state="disabled")

    def add_inner_style(self, entry):
        """Красивая мягкая рамка для крупных полей ввода"""
        entry.config(highlightbackground=self.border_color, highlightcolor=self.accent_color, highlightthickness=1)

    def open_pdf(self):
        self.input_path = filedialog.askopenfilename(filetypes=[("PDF Documents", "*.pdf")])
        if self.input_path:
            self.btn_open.config(text=f"📄   {os.path.basename(self.input_path)}", fg=self.accent_color)
            log_block(self.out, "FILE LOADED", os.path.basename(self.input_path), "ready")

    def analyze(self):
        if self.input_path:
            analyze_pdf(self.input_path, self.out)

    def resize(self):
        if not self.input_path:
            log_block(self.out, "ACTION REQUIRED", "Please choose a source PDF file first.", "alert")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not out_path:
            return
        try:
            wr = int(self.w_entry.get())
            hr = int(self.h_entry.get())
        except:
            log_block(self.out, "VALIDATION ERROR", "Aspect ratios must be integers (e.g. 1 and 1).", "failed")
            return
        
        resize_pdf_pure_python(self.input_path, out_path, wr, hr, self.out)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF Converter")
    root.geometry("680x760")
    root.minsize(680, 760)
    root.configure(bg="#F9F9FB")

    # Предотвращаем размытие текста при высоком DPI в Windows
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    setup_window_icon(root)

    App(root)
    root.mainloop()