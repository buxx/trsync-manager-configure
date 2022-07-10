import tkinter as tk
import argparse

from trsync.app import App


def main():
    parser = argparse.ArgumentParser(description="Trsync configuration window")
    parser.add_argument(
        "--password-setter-port",
        type=int,
        help="Set port here to use password setter instead raw password",
    )
    parser.add_argument(
        "--password-setter-token",
        type=str,
        help="If password setter used, set security access token here",
    )
    args = parser.parse_args()

    if args.password_setter_port:
        assert (
            args.password_setter_token is not None
        ), "You must provide --password-setter-token option if --password-setter-port given"

    root = tk.Tk()
    root.title("TrSync")
    root.geometry("375x450")
    app = App(
        root,
        password_setter_port=args.password_setter_port,
        password_setter_token=args.password_setter_token,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
