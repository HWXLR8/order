#!/usr/bin/env python3

import configparser
import tkinter as tk
from tkinter import messagebox
import os
import sys
import time
from escpos.printer import Network


class UI:
    def __init__(self, WIDTH, p):
        self.p = p

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
        button.grid(row=6, columnspan=2, pady=(0, 15))

        # keybindings
        root.bind("<Alt-i>", self.update_ip)
        root.bind("<Alt-I>", self.update_ip)
        root.bind("<Alt-s>", self.sendprint)
        root.bind("<Alt-S>", self.sendprint)
        root.bind("<Alt-c>", self.clear)
        root.bind("<Alt-C>", self.clear)
        root.mainloop()

    def clear(self, event=0):
        self.cnamebox.delete(0, tk.END)
        self.textbox.delete("1.0", tk.END)

    def sendprint(self, event=0):
        if not self.p:
            messagebox.showerror("Printer IP not set", "No printer IP is configured.\nPress Alt-I to set the IP address.")
            return

        name = self.namebox.get().upper()
        cust = self.cnamebox.get().upper()
        text = self.textbox.get("1.0", tk.END).upper()
        currenttime = time.strftime("%X")

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


WIDTH = 48  # width of receipt in chars
IP = read_config()["printer"].get("ip", "").strip()
p = Network(IP) if IP else None
if p:
    p.close()
ui = UI(WIDTH, p)
