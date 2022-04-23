import tkinter as tk

from trsync.app import App


def main():
    root = tk.Tk()
    root.geometry("600x450")
    app = App(root)
    app.mainloop()


if __name__ == "__main__":
    main()
