import tkinter as tk

class KeyboardPopup(tk.Toplevel):
    """On‑screen keyboard optimized for 480×240."""
    def __init__(self, master, target_entry, on_close_callback=None):
        super().__init__(master)
        self.title("Keyboard")
        self.geometry("480x240")
        self.resizable(False, False)
        self.target_entry = target_entry
        self.on_close_callback = on_close_callback
        self.input_var = tk.StringVar(value=target_entry.get())
        self.mode = 'lowercase'

        tk.Entry(self, textvariable=self.input_var, font=("Arial", 12)).pack(fill=tk.X, padx=5, pady=5)
        self.frame = tk.Frame(self)
        self.frame.pack()

        self.layouts = {
            'lowercase': [
                list("qwertyuiop"),
                list("asdfghjkl"),
                ['⇧']+list("zxcvbnm")+['⌫'],
                ['123','@','.',' ','Enter','Close']
            ],
            'uppercase': [
                list("QWERTYUIOP"),
                list("ASDFGHJKL"),
                ['⇧']+list("ZXCVBNM")+['⌫'],
                ['123','@','.',' ','Enter','Close']
            ],
            'symbols': [
                list("1234567890"),
                list("!@#$%^&*()"),
                ['ABC','-','=','_','+','{','}',':',"'",'⌫'],
                ['"',',','.','<','>','/','?',' ','Enter','Close']
            ]
        }
        self.render()

    def render(self):
        for w in self.frame.winfo_children(): w.destroy()
        for row in self.layouts[self.mode]:
            rowf = tk.Frame(self.frame)
            rowf.pack(fill=tk.X, pady=1)
            for key in row:
                tk.Button(
                    rowf, text=key, font=("Arial",10),
                    command=lambda k=key: self.on_key(k)
                ).pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=1, pady=1)

    def on_key(self, key):
        if key in ('⇧','123','ABC'):
            self.mode = {'⇧':'uppercase','123':'symbols','ABC':'lowercase'}[key]
            self.render()
        elif key == '⌫':
            self.input_var.set(self.input_var.get()[:-1])
        elif key == 'Enter':
            self.commit(); self.close()
        elif key == 'Close':
            self.close()
        else:
            self.input_var.set(self.input_var.get() + key)

    def commit(self):
        self.target_entry.delete(0,tk.END)
        self.target_entry.insert(0,self.input_var.get())

    def close(self):
        if self.on_close_callback: self.on_close_callback()
        self.destroy()
