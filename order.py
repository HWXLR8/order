#!/usr/bin/env python3

import argparse
import configparser
import tkinter as tk
from tkinter import messagebox
import os
import sys
import time
from escpos.printer import Network


class NullPrinter:
    """A no-op printer for when no printer IP is configured."""
    def open(self): pass
    def close(self): pass
    def image(self, path):
        print(f"[LOGO: {path}]")
    def set(self, align): pass
    def text(self, text):
        # Print to console instead of printer
        print(text.rstrip('\n'))
    def cut(self, mode="PART"): pass
    def buzzer(self, times=3, duration=5): pass


class UI:
    def __init__(self, WIDTH, p):
        self.p = p
        self.history = []  # In-memory history, capped at 100 entries

        root = tk.Tk()
        root.resizable(width=False, height=False)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=50)
        root.title("receipt printer")
        root.configure(background="#fafafa")

        # user name
        name_label = tk.Label(
            root,
            text="Your name:",
            anchor="w",
            background="#fafafa",
        )
        name_label.grid(row=0, column=0, sticky=tk.W, pady=(15, 0), padx=(14, 0))
        self.namebox = tk.Entry(root, width=20)
        self.namebox.grid(row=0, column=1, sticky=tk.W + tk.E, pady=(15, 0), padx=(0, 15))

        # customer name
        cname_label = tk.Label(
            root,
            text="Customer name:",
            anchor="w",
            background="#fafafa",
        )
        cname_label.grid(row=1, column=0, sticky=tk.W, pady=(15, 0), padx=(14, 0))
        self.cnamebox = tk.Entry(root, width=20)
        self.cnamebox.grid(row=1, column=1, sticky=tk.W + tk.E, pady=(15, 0), padx=(0, 15))

        # pick-up location
        self.pickupvar = tk.IntVar()
        pickup_label = tk.Label(
            root,
            text="Pick-up location:",
            anchor="w",
            background="#fafafa",
        )
        pickup_label.grid(row=2, column=0, sticky=tk.N, pady=(15, 0), padx=(14, 0))
        pickupframe = tk.Frame(root, background="#fafafa")
        pickupframe.grid(row=2, column=1, sticky="nesw", pady=(15, 0), padx=(0, 15))
        pickupfront = tk.Radiobutton(
            pickupframe,
            text="Front",
            background="#fafafa",
            anchor="w",
            variable=self.pickupvar,
            value=True,
        )
        pickupfront.pack(side="left")
        pickupfront.select()
        pickupback = tk.Radiobutton(
            pickupframe,
            text="Back",
            background="#fafafa",
            anchor="w",
            variable=self.pickupvar,
            value=False,
        )
        pickupback.pack(side="right")

        receipt_label = tk.Label(
            root,
            text="Enter what you would like to send to the printer:",
            background="#fafafa",
        )
        receipt_label.grid(row=4, columnspan=2, sticky=tk.W, pady=(15, 0), padx=(14, 0))

        # text box
        self.textbox = tk.Text(
            root,
            bd=2,
            relief=tk.RIDGE,
            width=WIDTH,
        )
        self.textbox.config(wrap=tk.WORD)
        self.textbox.grid(row=5, columnspan=2, pady=10, padx=10)

        # submit button
        button = tk.Button(
            root,
            text="Send to printer (Alt-s)",
            command=self.sendprint,
        )
        button.grid(row=6, columnspan=2, pady=(0, 5))

        # history button
        history_button = tk.Button(
            root,
            text="History (Alt-h)",
            command=self.show_history,
        )
        history_button.grid(row=7, columnspan=2, pady=(0, 15))

        # keybindings
        root.bind("<Alt-i>", self.update_ip)
        root.bind("<Alt-I>", self.update_ip)
        root.bind("<Alt-s>", self.sendprint)
        root.bind("<Alt-S>", self.sendprint)
        root.bind("<Alt-c>", self.clear)
        root.bind("<Alt-C>", self.clear)
        root.bind("<Alt-h>", self.show_history)
        root.bind("<Alt-H>", self.show_history)
        root.mainloop()

    def clear(self, event=0):
        self.cnamebox.delete(0, tk.END)
        self.textbox.delete("1.0", tk.END)

    def sendprint(self, event=0):
        name = self.namebox.get().upper()
        cust = self.cnamebox.get().upper()
        text = self.textbox.get("1.0", tk.END).upper()
        currenttime = time.strftime("%X")

        if isinstance(self.p, NullPrinter):
            # Null printer mode: print to console
            print("\n" + "=" * 50)
            print("PRINT JOB")
            print("=" * 50)
            print(f"Time: {currenttime}")
            print(f"Sent by: {name}")
            if cust:
                print(f"Customer: {cust}")
            print(f"Pickup: {'FRONT' if self.pickupvar.get() else 'BACK'}")
            print("-" * 50)
            print(text)
            print("-" * 50)
            print("PRINTED SUCCESSFULLY")
            print("=" * 50 + "\n")
        else:
            if not self.p:
                messagebox.showerror("Printer IP not set", "No printer IP is configured.\nPress Alt-I to set the IP address.")
                return

            try:
                self.p.open()
                self.p.image(resource_path("logo.png"))
                self.p.set("left")
                self.p.text("\n"*2)

                if self.pickupvar.get():
                    self.p.text("PICKUP: FRONT\n\n")
                else:
                    self.p.text("PICKUP: BACK\n\n")

                if cust:
                    self.p.text("CUSTOMER NAME: ")
                    self.p.text(cust + "\n")
                    self.p.text("_"*48)
                    self.p.text("\n"*2)

                self.p.text(text)
                self.p.text("\n"*10)
                self.p.text("SENT BY " + name + " @ " + currenttime)
                self.p.cut(mode="PART")
                self.p.buzzer(times=3, duration=5)

            except Exception as e:
                messagebox.showerror("Printer error", f"Could not print.\n\n{e}")
                return

            finally:
                try:
                    self.p.close()
                except Exception:
                    pass

        # only clear after a successful print
        self.textbox.delete("1.0", tk.END)
        self.cnamebox.delete(0, tk.END)

        # Add to history
        self.push_history(name, cust, self.pickupvar.get(), text.strip(), currenttime)

    def push_history(self, name, cust, pickup, text, timestamp):
        """Add order to history, capped at 100 entries."""
        order = {
            "name": name,
            "cust": cust,
            "pickup": pickup,
            "text": text,
            "timestamp": timestamp,
        }
        self.history.append(order)
        if len(self.history) > 100:
            self.history.pop(0)

    def show_history(self, event=0):
        """Show a popup window with past orders."""
        if not self.history:
            messagebox.showinfo("History", "No orders in history yet.")
            return

        popup = tk.Toplevel()
        popup.title("Order History")
        popup.geometry("500x400")

        # Listbox with scrollbar
        list_frame = tk.Frame(popup)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox with all orders (up to 100)
        display_orders = self.history
        for i, order in enumerate(display_orders):
            display_text = f"{i+1}. {order['timestamp']} - {order['name']}"
            if order['cust']:
                display_text += f" (Customer: {order['cust']})"
            listbox.insert(tk.END, display_text)

        # Select button
        select_button = tk.Button(
            popup,
            text="Select (Alt-s)",
            command=lambda: self.restore_order(listbox),
        )
        select_button.pack(pady=(0, 10))

        # Keybinding for selection
        popup.bind("<Alt-s>", lambda e: self.restore_order(listbox))
        popup.bind("<Alt-S>", lambda e: self.restore_order(listbox))
        popup.bind("<Escape>", lambda e: popup.destroy())

    def restore_order(self, listbox):
        """Restore selected order to the UI fields."""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select an order first.")
            return

        index = selection[0]
        # Get the actual index in history (display shows last 10)
        actual_index = len(self.history) - 10 + index
        if actual_index < 0:
            actual_index = index

        order = self.history[actual_index]

        # Restore fields
        self.namebox.delete(0, tk.END)
        self.namebox.insert(0, order['name'])

        self.cnamebox.delete(0, tk.END)
        if order['cust']:
            self.cnamebox.insert(0, order['cust'])

        self.pickupvar.set(1 if order['pickup'] else 0)

        self.textbox.delete("1.0", tk.END)
        self.textbox.insert("1.0", order['text'])


    def update_ip(self, event=0):
        def save_ip():
            new_ip = ip_entry.get().strip()
            config = configparser.ConfigParser()
            config.read(config_path())
            if "printer" not in config:
                config["printer"] = {}
            config["printer"]["ip"] = new_ip
            with open(config_path(), "w") as configfile:
                config.write(configfile)

            popup.destroy()

            if new_ip:
                self.p = Network(new_ip)
                self.p.close()
            else:
                self.p = None

        popup = tk.Toplevel()
        popup.title("Update IP Address")
        popup.geometry("300x100")
        # popup.attributes('-type', 'dialog')

        ip_label = tk.Label(popup, text="Enter new IP address:")
        ip_label.pack(pady=5)
        ip_entry = tk.Entry(popup)
        ip_entry.pack(pady=5)
        save_button = tk.Button(popup, text="Save", command=save_ip)
        save_button.pack(pady=5)


def config_path():
    base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "config.ini")


def read_config():
    config = configparser.ConfigParser()
    config.read(config_path())
    if "printer" not in config:
        config["printer"] = {}
    if "ip" not in config["printer"]:
        config["printer"]["ip"] = ""
    return config


def resource_path(path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)


def main():
    parser = argparse.ArgumentParser(description="Thermal receipt printer")
    parser.add_argument("--no-printer", action="store_true", help="Use null printer (prints to console instead of connecting)")
    args = parser.parse_args()

    WIDTH = 48  # width of receipt in chars
    IP = read_config()["printer"].get("ip", "").strip()

    if args.no_printer or not IP:
        # No printer configured or --no-printer flag: use null printer
        p = NullPrinter()
    else:
        # Real printer mode
        p = Network(IP)
        if p:
            p.close()

    ui = UI(WIDTH, p)


if __name__ == "__main__":
    main()
