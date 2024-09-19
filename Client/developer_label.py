import webbrowser
from tkinter import Label, Frame

class DeveloperLabel:
    def __init__(self, parent, font, light_theme, dark_theme):
        self.parent = parent
        self.font = font
        self.light_theme = light_theme
        self.dark_theme = dark_theme
        self.current_theme = 'light'

        self.frame = Frame(self.parent)
        self.frame.pack(side='right')  # Changed from 'bottom' to 'right'

        self.label = Label(
            self.frame,
            text="Developed by AbdulAhad",
            font=(self.font, 10, "bold","italic"),
            cursor="hand2"
        )
        self.label.pack(side='right', padx=10, pady=5)
        self.label.bind("<Button-1>", self.open_portfolio)

        self.update_theme(self.current_theme)

    def open_portfolio(self, event):
        webbrowser.open("https://ahad324.github.io/AllProjects/")

    def update_theme(self, theme):
        self.current_theme = theme
        colors = self.light_theme if theme == 'light' else self.dark_theme
        self.frame.config(bg=colors['bg'])
        self.label.config(bg=colors['bg'], fg=colors['fg'])

def create_developer_label(parent, font, light_theme, dark_theme):
    return DeveloperLabel(parent, font, light_theme, dark_theme)