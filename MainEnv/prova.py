import tkinter as tk

def create_tooltip(widget, text):
    tooltip_window = None

    def show_tooltip(event):
        nonlocal tooltip_window
        if tooltip_window is not None:
            return
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip_window = tk.Toplevel(widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tooltip_window, text=text, background="yellow", borderwidth=1, relief="solid")
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip_window
        if tooltip_window is not None:
            tooltip_window.destroy()
            tooltip_window = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def main():
    root = tk.Tk()
    root.title("Esempio di Tooltip")

    info_icon = tk.Label(root, text="ℹ️", font=("Arial", 24))  # Usa un'icona di info
    info_icon.pack(pady=20)

    create_tooltip(info_icon, "Questo è un tooltip informativo!")

    root.mainloop()

if __name__ == "__main__":
    main()
