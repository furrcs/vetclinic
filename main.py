import psycopg2
from psycopg2.extras import RealDictCursor
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime

tables = {
    "Appointments": (
        ["appointment_id", "pet", "client", "employee", "appointment_date", "status"],
        ["ID", "Питомец", "Кто привёл", "Врач", "Дата", "Статус"]
    ),
    "Payments": (
        ["payment_id", "appointment_date", "payment_date", "employee", "client", "payment_method", "amount", "status"],
        ["ID", "Приём", "Дата оплаты", "Кто принял", "Кто оплатил", "Метод", "Сумма", "Статус"]
    ),
    "Clients": (
        ["client_id", "client", "phone", "email"],
        ["ID", "ФИО", "Телефон", "Почта"]
    ),
    "Pets": (
        ["pet_id", "name", "pet_type", "breed", "gender", "color", "birth_date"],
        ["ID", "Кличка", "Вид", "Порода", "Пол", "Окрас", "Дата рождения"]
    ),
    "Employees": (
        ["employee_id", "employee", "phone", "email", "role"],
        ["ID", "ФИО", "Телефон", "Почта", "Роль"]
    ),
    "Breeds": (
        ["breed_id", "pet_type", "name"],
        ["ID", "Тип животного", "Название"]
    ),
    "Suppliers": (
        ["supplier_id", "company_name", "phone", "email", "address"],
        ["ID", "Название компании", "Телефон", "Почта", "Адрес"]
    ),
    "Services": (
        ["service_id", "name", "price"],
        ["ID", "Название", "Цена"]
    ),
    "Medicines": (
        ["medicine_id", "name", "price", "supplier", "unit", "stock"],
        ["ID", "Название", "Цена", "Поставщик", "Единица измерения", "Остаток"]
    )
}

def apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except Exception:
        style.theme_use("clam")

    FONT = "Segoe UI"
    FONT_SIZE = 12

    style.configure(".", font=(FONT, FONT_SIZE))
    style.configure("TLabel", font=(FONT, FONT_SIZE))
    style.configure("TButton", font=(FONT, FONT_SIZE), padding=(5, 5))
    style.configure("TEntry", font=(FONT, FONT_SIZE), padding=5)
    style.configure("TCombobox", font=(FONT, FONT_SIZE), padding=5)
    style.configure("Treeview", font=(FONT, FONT_SIZE), rowheight=30)
    style.configure("Treeview.Heading", font=(FONT, FONT_SIZE, "bold"))
    style.configure("TNotebook.Tab", font=(FONT, FONT_SIZE), padding=(30, 5))
    style.configure("Heading.TLabel", font=(FONT, 14, "bold"))
    style.configure("Total.TLabel", font=(FONT, FONT_SIZE, "bold"))

def treeview_with_scroll(parent, keys, labels, height=18):
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=keys, show="headings", height=height)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    for key, label in zip(keys, labels):
        tree.heading(key, text=label)
        tree.column(key, width=120, minwidth=80, stretch=True)
    tree.pack(side=LEFT, fill=BOTH, expand=True)
    scroll.pack(side=RIGHT, fill=Y)
    return frame, tree

class BaseToplevel(Toplevel):
    toplevel_title = None
    toplevel_geometry = None
    fields = []
    table_name = None
    pk_column = None

    def __init__(self, parent, db, record=None, on_success=None, pk_column=None):
        super().__init__(parent)
        self.db = db
        self.geometry(self.toplevel_geometry)
        self.record = record
        self.on_success = on_success
        if pk_column is not None:
            self.pk_column = pk_column
        self.entries = {}
        self.combo_maps = {}

        self.title(self.toplevel_title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.entries_frame = ttk.Frame(self)
        self.entries_frame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

        self.btns_frame = ttk.Frame(self)
        self.btns_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        self.build_form()

        if self.record is not None:
            for field in self.fields:
                self._fill_field(field)

        ttk.Button(self.btns_frame, text="Сохранить", command=self.save).pack(side=LEFT, padx=5)
        ttk.Button(self.btns_frame, text="Отмена", command=self.destroy).pack(side=LEFT, padx=5)

    def build_form(self):
        for i, field in enumerate(self.fields):
            label = field["label"]
            attr = field["attr"]
            field_type = field.get("type", "entry")
            required = field.get("required", False)

            text = f"{label} *" if required else label
            ttk.Label(self.entries_frame, text=text).grid(row=i, column=0, sticky=W, pady=4, padx=(0, 10))

            if field_type == "combo":
                widget = self._build_combo(field)
            else:
                widget = self._build_entry(field)

            widget.grid(row=i, column=1, sticky=EW, pady=4)
            self.entries[attr] = widget

        self.entries_frame.columnconfigure(1, weight=1)

    def _build_combo(self, field):
        attr = field["attr"]
        combo = ttk.Combobox(self.entries_frame, width=28, state="readonly")

        if "source" in field:
            rows = getattr(self.db, field["source"])()
            display_key = field.get("display", "name")
            value_key = field.get("value", field["attr"])
            self.combo_maps[attr] = {r[display_key]: r[value_key] for r in rows}
            combo["values"] = list(self.combo_maps[attr].keys())

        elif "values" in field:
            combo["values"] = field["values"]
            self.combo_maps[attr] = {v: v for v in field["values"]}

        return combo

    def _build_entry(self, field):
        entry = ttk.Entry(self.entries_frame, width=30)

        if field.get("type") == "number":
            entry.configure(validate="key", validatecommand=(self.register(self._only_number), "%P"))
        return entry

    def _only_number(self, value):
        if value == "":
            return True
        if value == "-":
            return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    def collect_value(self, field):
        attr = field["attr"]
        field_type = field.get("type", "entry")
        widget = self.entries[attr]
        raw = widget.get().strip()

        if field_type == "combo" and raw:
            mapping = self.combo_maps.get(attr, {})

            if raw not in mapping:
                raise ValueError(f"Значение '{raw}' не найдено в списке {field['label']}")
            return mapping[raw]

        if field_type == "date" and raw:
            try:
                return datetime.strptime(raw, "%d.%m.%Y").date()
            except ValueError:
                raise ValueError(f"Неверный формат даты: {raw}. Ожидается ДД.ММ.ГГГГ")

        if field_type == "datetime" and raw:
            try:
                return datetime.strptime(raw, "%d.%m.%Y %H:%M")
            except ValueError:
                raise ValueError(f"Неверный формат: {raw}. Ожидается ДД.ММ.ГГГГ ЧЧ:ММ")

        return raw or None

    def _fill_field(self, field):
        attr = field["attr"]
        field_type = field.get("type", "entry")
        value = self.record.get(attr)
        if value is None:
            return
        widget = self.entries[attr]

        if field_type == "combo":
            reverse = {v: d for d, v in self.combo_maps.get(attr, {}).items()}
            display = reverse.get(value)
            if display is not None:
                widget.set(display)
        elif field_type == "date":
            widget.delete(0, "end")
            widget.insert(0, value.strftime("%d.%m.%Y"))
            widget.configure(foreground="black")
        elif field_type == "datetime":
            widget.delete(0, "end")
            widget.insert(0, value.strftime("%d.%m.%Y %H:%M"))
            widget.configure(foreground="black")
        else:
            widget.delete(0, "end")
            widget.insert(0, str(value))

    def save(self):
        data = {}
        try:
            for field in self.fields:
                value = self.collect_value(field)
                if field.get("required") and not value:
                    messagebox.showerror("Ошибка", f"Заполните: {field['label']}", parent=self)
                    return
                data[field["attr"]] = value

            if self.record is None:
                self.db.insert(self.table_name, **data)
            else:
                pk_value = self.record[self.pk_column]
                self.db.update(self.table_name, self.pk_column, pk_value, **data)

        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class BaseListToplevel(Toplevel):
    toplevel_title = None
    toplevel_geometry = None

    def __init__(self, parent, db, on_success=None):
        super().__init__(parent)
        self.db = db
        self.on_success = on_success

        self.title(self.toplevel_title)
        self.geometry(self.toplevel_geometry)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.btns_frame = ttk.Frame(self)
        self.btns_frame.pack(fill=X, padx=10, pady=(0, 10))

        self.build_content()
        self.build_buttons(self.btns_frame)

    def build_content(self):
        raise NotImplementedError

    def build_buttons(self, btns):
        raise NotImplementedError

    def close(self):
        if self.on_success:
            self.on_success()
        self.destroy()

class BaseTab(ttk.Frame):
    table_name = None
    pk_column = None
    buttons = []
    toplevel_class = None

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        keys, labels = tables[self.table_name]
        self.frame_tree, self.tree = treeview_with_scroll(self, keys, labels)
        self.frame_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.btns = ttk.Frame(self)
        self.btns.pack(fill=X, side=BOTTOM, pady=5)
        for label, cmd in self.buttons:
            ttk.Button(self.btns, text=label, width=15, command=cmd).pack(side=LEFT, padx=10)

        self.load_data()

    def fetch(self):
        raise NotImplementedError

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        keys, _ = tables[self.table_name]
        for row in self.fetch():
            self.tree.insert("", "end", values=[row[key] or "—" for key in keys])

    def open_create(self):
        dlg = self.toplevel_class(self.winfo_toplevel(), self.db, record=None, on_success=self.load_data)
        self.wait_window(dlg)

    def open_edit(self):
        record = self._get_selected_record()
        if not record:
            return

        dlg = self.toplevel_class(self.winfo_toplevel(), self.db, record=record, on_success=self.load_data, pk_column=self.pk_column)
        self.wait_window(dlg)

    def open_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите строку", parent=self)
            return

        values = self.tree.item(sel[0])["values"]
        pk_value = values[0]

        if not messagebox.askyesno("Подтверждение", f"Удалить запись ID={pk_value}?", parent=self):
            return

        try:
            self.db.delete(self.table_name, self.pk_column, pk_value)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_data()

    def _get_selected_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите строку", parent=self)
            return None

        values = self.tree.item(sel[0])["values"]
        pk_value = values[0]

        record = self.db.get_by_id(self.table_name, self.pk_column, pk_value)
        if not record:
            messagebox.showerror("Ошибка", "Запись не найдена", parent=self)
            return None
        return record

class AppointmentsToplevel(BaseToplevel):
    toplevel_title = "Новый приём"
    table_name = "Appointments"
    fields = [
        {"label": "Клиент",                  "attr": "client_id",        "type": "combo",    "source": "get_clients", "display": "client",   "required": True},
        {"label": "Питомец",                 "attr": "pet_id",           "type": "combo",    "source": "get_pets",    "display": "name",     "required": True},
        {"label": "Врач",                    "attr": "employee_id",      "type": "combo",    "source": "get_doctors", "display": "employee", "required": True},
        {"label": "Дата (ДД.ММ.ГГГГ ЧЧ:ММ)", "attr": "appointment_date", "type": "datetime", "required": True}
    ]

class AppointmentServicesToplevel(BaseListToplevel):
    toplevel_title = "Услуги приёма"

    def __init__(self, parent, db, appointment_id, on_success=None):
        self.appointment_id = appointment_id
        super().__init__(parent, db, on_success=on_success)

    def build_content(self):
        ttk.Label(self.main_frame, text=f"Услуги приёма №{self.appointment_id}", style="Heading.TLabel").pack(anchor=W, pady=(0, 10))

        self.frame_tree, self.tree = treeview_with_scroll(self.main_frame, keys=["service_id", "name", "quantity", "price", "total"], labels=["ID", "Услуга", "Кол-во", "Цена", "Сумма"], height=12)
        self.frame_tree.pack(fill=BOTH, expand=True)

        self.total_label = ttk.Label(self.main_frame, text="", style="Total.TLabel")
        self.total_label.pack(anchor=E, pady=(10, 0))

        self.load_services()

    def build_buttons(self, btns):
        ttk.Button(btns, text="Добавить", command=self.add_service).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Удалить",  command=self.remove_service).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Закрыть",  command=self.close).pack(side=RIGHT, padx=5)

    def load_services(self):
        self.tree.delete(*self.tree.get_children())
        total = 0.0

        for row in self.db.get_appointment_services(self.appointment_id):
            row_total = float(row["price"]) * row["quantity"]
            total += row_total

            self.tree.insert("", "end", values=(
                row["service_id"],
                row["name"],
                row["quantity"],
                f"{row['price']:.2f}",
                f"{row_total:.2f}",
            ))

        self.total_label.config(text=f"Итого по услугам: {total:.2f} руб.")

    def add_service(self):
        dlg = AddServiceToAppointmentToplevel(self.winfo_toplevel(), self.db, appointment_id=self.appointment_id, on_success=self.load_services)
        self.wait_window(dlg)

    def remove_service(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите услугу", parent=self)
            return

        values = self.tree.item(sel[0])["values"]
        service_id = values[0]
        service_name = values[1]

        if not messagebox.askyesno("Подтверждение", f"Удалить услугу «{service_name}» с приёма?", parent=self):
            return

        try:
            self.db.remove_service_from_appointment(self.appointment_id, service_id)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_services()

class AddServiceToAppointmentToplevel(Toplevel):
    def __init__(self, parent, db, appointment_id, on_success=None):
        super().__init__(parent)
        self.db = db
        self.appointment_id = appointment_id
        self.on_success = on_success

        self.title("Добавить услугу")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Услуга:").grid(row=0, column=0, sticky=W, pady=5)
        self.combo_service = ttk.Combobox(frame, width=35, state="readonly")
        self.combo_service.grid(row=0, column=1, sticky=EW, pady=5)

        self.service_map = {}
        for row in db.get_services_not_in_appointment(appointment_id):
            self.service_map[row["name"]] = row["service_id"]
        self.combo_service["values"] = list(self.service_map.keys())
        if self.combo_service["values"]:
            self.combo_service.set(self.combo_service["values"][0])

        ttk.Label(frame, text="Количество:").grid(row=1, column=0, sticky=W, pady=5)
        self.entry_qty = ttk.Entry(frame, width=35)
        self.entry_qty.insert(0, "1")
        self.entry_qty.grid(row=1, column=1, sticky=EW, pady=5)

        ttk.Label(frame, text="Цена:").grid(row=2, column=0, sticky=W, pady=5)
        self.label_price = ttk.Label(frame, text="—", style="Total.TLabel")
        self.label_price.grid(row=2, column=1, sticky=W, pady=5)

        self.combo_service.bind("<<ComboboxSelected>>", self.update_price)
        self.update_price()

        frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=X, padx=15, pady=10)

        ttk.Button(btns, text="Добавить", command=self.add).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="Отмена",   command=self.destroy).pack(side=RIGHT, padx=5)

    def update_price(self, event=None):
        service_display = self.combo_service.get()
        if not service_display:
            self.label_price.config(text="—")
            return

        service_id = self.service_map[service_display]
        service = self.db.get_by_id("Services", "service_id", service_id)
        if service:
            self.label_price.config(text=f"{service['price']} руб.")

    def add(self):
        service_display = self.combo_service.get()
        if not service_display:
            messagebox.showerror("Ошибка", "Выберите услугу", parent=self)
            return

        try:
            qty = int(self.entry_qty.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом", parent=self)
            return

        service_id = self.service_map[service_display]

        try:
            self.db.add_service_to_appointment(self.appointment_id, service_id, qty)
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class AppointmentMedicinesToplevel(BaseListToplevel):
    toplevel_title = "Лекарства приёма"

    def __init__(self, parent, db, appointment_id, on_success=None):
        self.appointment_id = appointment_id
        super().__init__(parent, db, on_success=on_success)

    def build_content(self):
        ttk.Label(self.main_frame, text=f"Лекарства приёма №{self.appointment_id}", style="Heading.TLabel").pack(anchor=W, pady=(0, 10))

        self.frame_tree, self.tree = treeview_with_scroll(self.main_frame, keys=["medicine_id", "name", "quantity", "dosage", "price", "total"], labels=["ID", "Лекарство", "Кол-во", "Дозировка", "Цена", "Сумма"], height=12)
        self.frame_tree.pack(fill=BOTH, expand=True)

        self.total_label = ttk.Label(self.main_frame, text="", style="Total.TLabel")
        self.total_label.pack(anchor=E, pady=(10, 0))

        self.load_medicines()

    def build_buttons(self, btns):
        ttk.Button(btns, text="Добавить", command=self.add_medicine).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Удалить",  command=self.remove_medicine).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Закрыть",  command=self.close).pack(side=RIGHT, padx=5)

    def load_medicines(self):
        self.tree.delete(*self.tree.get_children())
        total = 0.0

        for row in self.db.get_appointment_medicines(self.appointment_id):
            row_total = float(row["price"]) * row["quantity"]
            total += row_total

            self.tree.insert("", "end", values=(
                row["medicine_id"],
                row["name"],
                row["quantity"],
                row["dosage"] or "—",
                f"{row['price']:.2f}",
                f"{row_total:.2f}",
            ))

        self.total_label.config(text=f"Итого по лекарствам: {total:.2f} руб.")

    def add_medicine(self):
        dlg = AddMedicineToAppointmentToplevel(self.winfo_toplevel(), self.db, appointment_id=self.appointment_id, on_success=self.load_medicines)
        self.wait_window(dlg)

    def remove_medicine(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите лекарство", parent=self)
            return

        values = self.tree.item(sel[0])["values"]
        medicine_id = values[0]
        medicine_name = values[1]
        quantity = values[2]

        if not messagebox.askyesno("Подтверждение",
            f"Удалить лекарство «{medicine_name}» с приёма?\n"
            f"Остаток на складе будет увеличен на {quantity}.",
            parent=self,
        ):
            return

        try:
            self.db.remove_medicine_from_appointment(self.appointment_id, medicine_id)
            self.db.update_stock(medicine_id, int(quantity))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_medicines()

class AddMedicineToAppointmentToplevel(Toplevel):
    def __init__(self, parent, db, appointment_id, on_success=None):
        super().__init__(parent)
        self.db = db
        self.appointment_id = appointment_id
        self.on_success = on_success

        self.title("Добавить лекарство")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Лекарство:").grid(row=0, column=0, sticky=W, pady=5)
        self.combo_medicine = ttk.Combobox(frame, width=35, state="readonly")
        self.combo_medicine.grid(row=0, column=1, sticky=EW, pady=5)

        self.medicine_map = {}
        self.medicine_info = {}

        for row in db.get_medicines_not_in_appointment(appointment_id):
            display = f"{row['name']} (ост. {row['stock']})"
            self.medicine_map[display] = row["medicine_id"]
            self.medicine_info[row["medicine_id"]] = {
                "price": row["price"],
                "stock": row["stock"],
            }

        self.combo_medicine["values"] = list(self.medicine_map.keys())
        if self.combo_medicine["values"]:
            self.combo_medicine.set(self.combo_medicine["values"][0])

        ttk.Label(frame, text="Количество:").grid(row=1, column=0, sticky=W, pady=5)
        self.entry_qty = ttk.Entry(frame, width=35)
        self.entry_qty.insert(0, "1")
        self.entry_qty.grid(row=1, column=1, sticky=EW, pady=5)

        ttk.Label(frame, text="Дозировка:").grid(row=2, column=0, sticky=W, pady=5)
        self.entry_dosage = ttk.Entry(frame, width=35)
        self.entry_dosage.grid(row=2, column=1, sticky=EW, pady=5)

        ttk.Label(frame, text="Цена:").grid(row=3, column=0, sticky=W, pady=5)
        self.label_price = ttk.Label(frame, text="—", style="Total.TLabel")
        self.label_price.grid(row=3, column=1, sticky=W, pady=5)

        ttk.Label(frame, text="Остаток:").grid(row=4, column=0, sticky=W, pady=5)
        self.label_stock = ttk.Label(frame, text="—")
        self.label_stock.grid(row=4, column=1, sticky=W, pady=5)

        self.combo_medicine.bind("<<ComboboxSelected>>", self.update_info)
        self.update_info()

        frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=X, padx=15, pady=10)

        ttk.Button(btns, text="Добавить", command=self.add).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="Отмена",   command=self.destroy).pack(side=RIGHT, padx=5)

    def update_info(self, event=None):
        display = self.combo_medicine.get()
        if not display:
            self.label_price.config(text="—")
            self.label_stock.config(text="—")
            return

        medicine_id = self.medicine_map[display]
        info = self.medicine_info[medicine_id]
        self.label_price.config(text=f"{info['price']} руб.")
        self.label_stock.config(text=str(info["stock"]))

    def add(self):
        display = self.combo_medicine.get()
        if not display:
            messagebox.showerror("Ошибка", "Выберите лекарство", parent=self)
            return

        try:
            qty = int(self.entry_qty.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом", parent=self)
            return

        medicine_id = self.medicine_map[display]
        info = self.medicine_info[medicine_id]

        if qty > info["stock"]:
            messagebox.showerror("Ошибка", f"На складе только {info['stock']} ед. Нельзя списать {qty}.", parent=self)
            return

        dosage = self.entry_dosage.get().strip() or None

        try:
            self.db.add_medicine_to_appointment(self.appointment_id, medicine_id, qty, dosage)
            self.db.update_stock(medicine_id, -qty)
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class MedicalRecordToplevel(BaseToplevel):
    toplevel_title = "Медкарта"
    toplevel_geometry = "800x400"
    table_name = "Medical_records"
    pk_column = "record_id"
    fields = [
        {"label": "Причина обращения", "attr": "reason",          "required": False},
        {"label": "Диагноз",           "attr": "diagnosis",       "required": True},
        {"label": "Температура (°C)",  "attr": "temperature",     "type": "number", "required": False},
        {"label": "Вес (кг)",          "attr": "weight",          "type": "number", "required": False},
        {"label": "Рекомендации",      "attr": "recommendations", "required": False},
        {"label": "Описание",          "attr": "description",     "required": False},
    ]

    def __init__(self, parent, db, appointment_id, record=None, on_success=None):
        self.appointment_id = appointment_id
        super().__init__(parent, db, record=record, on_success=on_success)

    def save(self):
        data = {}
        try:
            for field in self.fields:
                value = self.collect_value(field)
                if field.get("required") and not value:
                    raise ValueError(f"Заполните: {field['label']}")
                data[field["attr"]] = value

            if self.record is None:
                self.db.create_medical_record(
                    appointment_id=self.appointment_id,
                    reason=data.get("reason"),
                    diagnosis=data.get("diagnosis"),
                    temperature=data.get("temperature"),
                    weight=data.get("weight"),
                    recommendations=data.get("recommendations"),
                    description=data.get("description"),
                )
            else:
                pk_value = self.record[self.pk_column]
                self.db.update_medical_record(
                    record_id=pk_value,
                    reason=data.get("reason"),
                    diagnosis=data.get("diagnosis"),
                    temperature=data.get("temperature"),
                    weight=data.get("weight"),
                    recommendations=data.get("recommendations"),
                    description=data.get("description"),
                )

        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class PaymentAcceptToplevel(Toplevel):
    def __init__(self, parent, db, payment, on_success=None):
        super().__init__(parent)
        self.db = db
        self.payment = payment
        self.on_success = on_success

        self.title("Принять оплату")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Сумма:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Label(frame, text=f"{self.payment['amount']} руб.", style="Total.TLabel").grid(row=0, column=1, sticky=W, pady=5)

        ttk.Label(frame, text="Кто оплатил:").grid(row=1, column=0, sticky=W, pady=5)
        self.combo_client = ttk.Combobox(frame, width=28, state="readonly")
        self.combo_client.grid(row=1, column=1, sticky=EW, pady=5)

        self.client_map = {}
        for row in db.get_clients():
            self.client_map[row["client"]] = row["client_id"]
        self.combo_client["values"] = list(self.client_map.keys())

        reverse = {v: k for k, v in self.client_map.items()}
        current_client = reverse.get(self.payment["client_id"])
        if current_client:
            self.combo_client.set(current_client)

        ttk.Label(frame, text="Метод оплаты:").grid(row=2, column=0, sticky=W, pady=5)
        self.combo_method = ttk.Combobox(frame, width=28, state="readonly", values=["наличные", "карта", "перевод"])
        self.combo_method.grid(row=2, column=1, sticky=EW, pady=5)
        self.combo_method.set("наличные")

        ttk.Label(frame, text="Кто принял:").grid(row=3, column=0, sticky=W, pady=5)
        self.combo_employee = ttk.Combobox(frame, width=28, state="readonly")
        self.combo_employee.grid(row=3, column=1, sticky=EW, pady=5)

        self.employee_map = {}
        for row in db.get_receptionists():
            self.employee_map[row["employee"]] = row["employee_id"]
        self.combo_employee["values"] = list(self.employee_map.keys())
        if self.combo_employee["values"]:
            self.combo_employee.set(self.combo_employee["values"][0])

        frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=X, padx=15, pady=10)

        ttk.Button(btns, text="Принять", command=self.accept).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side=RIGHT, padx=5)

    def accept(self):
        client_display = self.combo_client.get()
        method = self.combo_method.get()
        employee_display = self.combo_employee.get()

        if not client_display or not method or not employee_display:
            messagebox.showerror("Ошибка", "Заполните все поля", parent=self)
            return

        client_id = self.client_map[client_display]
        employee_id = self.employee_map[employee_display]

        try:
            self.db.complete_payment(payment_id=self.payment["payment_id"], client_id=client_id, employee_id=employee_id, payment_method=method,)
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class ClientsToplevel(BaseToplevel):
    toplevel_title = "Новый клиент"
    table_name = "Clients"
    fields = [
        {"label": "Фамилия",  "attr": "surname",    "required": True},
        {"label": "Имя",      "attr": "name",       "required": True},
        {"label": "Отчество", "attr": "third_name", "required": False},
        {"label": "Телефон",  "attr": "phone",      "required": True},
        {"label": "Почта",    "attr": "email",      "required": False},
    ]

class PetsToplevel(BaseToplevel):
    toplevel_title = "Новый питомец"
    table_name = "Pets"
    fields = [
        {"label": "Кличка",                     "attr": "name",       "type": "entry", "required": True},
        {"label": "Порода",                     "attr": "breed_id",   "type": "combo", "source": "get_breeds", "display": "name", "required": True},
        {"label": "Пол",                        "attr": "gender",     "type": "combo", "values": ["самец", "самка"], "required": True},
        {"label": "Окрас",                      "attr": "color",      "type": "entry", "required": False},
        {"label": "Дата рождения (ДД.ММ.ГГГГ)", "attr": "birth_date", "type": "date",  "required": False},
    ]

class ClientPetsToplevel(BaseListToplevel):
    toplevel_title = "Питомцы клиента"
    toplevel_geometry = "1000x500"
    table_name = "Pets"

    def __init__(self, parent, db, client, on_success=None):
        self.client = client
        super().__init__(parent, db, on_success=on_success)

    def build_content(self):
        fio = f"{self.client['surname']} {self.client['name']}"
        if self.client.get("third_name"):
            fio += f" {self.client['third_name']}"

        ttk.Label(self.main_frame, text=f"Клиент: {fio}", style="Heading.TLabel").pack(anchor=W, pady=(0, 10))

        keys, labels = tables[self.table_name]
        self.frame_tree, self.tree = treeview_with_scroll(self.main_frame, keys, labels, height=12)
        self.frame_tree.pack(fill=BOTH, expand=True)

        self.load_pets()

    def build_buttons(self, btns):
        ttk.Button(btns, text="Привязать", command=self.add_pet).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Отвязать", command=self.remove_pet).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Закрыть",  command=self.close).pack(side=RIGHT, padx=5)

    def load_pets(self):
        self.tree.delete(*self.tree.get_children())
        keys, _ = tables[self.table_name]
        for row in self.db.get_pets_by_client(self.client["client_id"]):
            self.tree.insert("", "end", values=[row[k] or "—" for k in keys])

    def add_pet(self):
        dlg = AddPetToClientToplevel(self.winfo_toplevel(), self.db, client_id=self.client["client_id"], on_success=self.load_pets)
        self.wait_window(dlg)

    def remove_pet(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите питомца", parent=self)
            return

        values = self.tree.item(sel[0])["values"]
        pet_id = values[0]
        pet_name = values[1]

        if not messagebox.askyesno("Подтверждение", f"Отвязать питомца «{pet_name}» от клиента?", parent=self):
            return

        try:
            self.db.unlink_pet_from_client(self.client["client_id"], pet_id)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_pets()

class AddPetToClientToplevel(Toplevel):
    def __init__(self, parent, db, client_id, on_success=None):
        super().__init__(parent)
        self.db = db
        self.client_id = client_id
        self.on_success = on_success

        self.title("Добавить питомца")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Питомец:").grid(row=0, column=0, sticky=W, pady=5)
        self.combo = ttk.Combobox(frame, width=35, state="readonly")
        self.combo.grid(row=0, column=1, sticky=EW, pady=5)

        self.pet_map = {}
        for row in db.get_pets_not_by_client(client_id):
            self.pet_map[row["name"]] = row["pet_id"]
        self.combo["values"] = list(self.pet_map.keys())
        if self.combo["values"]:
            self.combo.set(self.combo["values"][0])

        frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=X, padx=15, pady=10)

        ttk.Button(btns, text="Добавить", command=self.add).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="Отмена",   command=self.destroy).pack(side=RIGHT, padx=5)

    def add(self):
        pet_display = self.combo.get()
        if not pet_display:
            messagebox.showerror("Ошибка", "Выберите питомца", parent=self)
            return

        pet_id = self.pet_map[pet_display]

        try:
            self.db.link_pet_to_client(self.client_id, pet_id)
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        if self.on_success:
            self.on_success()
        self.destroy()

class EmployeesToplevel(BaseToplevel):
    toplevel_title = "Новый сотрудник"
    table_name = "Employees"
    fields = [
        {"label": "Фамилия",   "attr": "surname",    "required": True},
        {"label": "Имя",       "attr": "name",       "required": True},
        {"label": "Отчество",  "attr": "third_name", "required": False},
        {"label": "Телефон",   "attr": "phone",      "required": True},
        {"label": "Почта",     "attr": "email",      "required": False},
        {"label": "Роль",      "attr": "role",       "type": "combo", "values": ["admin", "doctor", "assistant", "receptionist"], "required": True},
    ]

class BreedsToplevel(BaseToplevel):
    toplevel_title = "Новая порода"
    table_name = "Breeds"
    fields = [
        {"label": "Тип животного", "attr": "pet_type", "type": "combo", "values": ["кошка", "собака", "птица", "грызун"], "required": True},
        {"label": "Название",      "attr": "name",     "required": True},
    ]

class SuppliersToplevel(BaseToplevel):
    toplevel_title = "Новый поставщик"
    table_name = "Suppliers"
    fields = [
        {"label": "Название компании", "attr": "company_name", "required": True},
        {"label": "Телефон",           "attr": "phone",        "required": True},
        {"label": "Почта",             "attr": "email",        "required": False},
        {"label": "Адрес",             "attr": "address",      "required": False},
    ]

class ServicesToplevel(BaseToplevel):
    toplevel_title = "Новая услуга"
    table_name = "Services"
    fields = [
        {"label": "Название", "attr": "name",  "required": True},
        {"label": "Цена",     "attr": "price", "type": "number", "required": True},
    ]

class MedicinesToplevel(BaseToplevel):
    toplevel_title = "Медикамент"
    table_name = "Medicines"
    fields = [
        {"label": "Название",          "attr": "name",        "required": True},
        {"label": "Цена",              "attr": "price",       "type": "number", "required": True},
        {"label": "Поставщик",         "attr": "supplier_id", "type": "combo", "source": "get_suppliers", "display": "company_name", "required": False},
        {"label": "Единица измерения", "attr": "unit",        "required": False},
        {"label": "Остаток",           "attr": "stock", "type": "number", "required": False},
    ]

class AppointmentsTab(BaseTab):
    table_name = "Appointments"
    pk_column = "appointment_id"
    toplevel_class = AppointmentsToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete),
            ("Отменить", self.cancel),
            ("Услуги", self.manage_services),
            ("Медикаменты", self.manage_medicines),
            ("Медкарта", self.medical_record),
            ("Провести", self.complete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_appointments()

    def cancel(self):
        record = self._get_selected_record()
        if not record:
            return
        if record["status"] != "запланирован":
            messagebox.showwarning("Внимание", "Отменить можно только запланированный приём", parent=self)
            return

        if not messagebox.askyesno("Подтверждение", "Отменить приём?", parent=self):
            return

        try:
            self.db.update_appointment_status(record["appointment_id"], "отменён")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_data()

    def manage_services(self):
            record = self._get_selected_record()
            if not record:
                return

            dlg = AppointmentServicesToplevel(self.winfo_toplevel(), self.db, appointment_id=record["appointment_id"], on_success=self.load_data)
            self.wait_window(dlg)

    def manage_medicines(self):
            record = self._get_selected_record()
            if not record:
                return

            dlg = AppointmentMedicinesToplevel(self.winfo_toplevel(), self.db, appointment_id=record["appointment_id"], on_success=self.load_data)
            self.wait_window(dlg)

    def medical_record(self):
            record = self._get_selected_record()
            if not record:
                return

            existing = self.db.get_medical_records(record["appointment_id"])
            med_record = existing[0] if existing else None

            dlg = MedicalRecordToplevel(self.winfo_toplevel(), self.db, appointment_id=record["appointment_id"], record=med_record, on_success=self.load_data)
            self.wait_window(dlg)

    def complete(self):
        record = self._get_selected_record()
        if not record:
            return
        if record["status"] != "запланирован":
            messagebox.showwarning("Внимание", "Провести можно только запланированный приём", parent=self)
            return

        services = self.db.get_appointment_services(record["appointment_id"])
        medicines = self.db.get_appointment_medicines(record["appointment_id"])
        if not services and not medicines:
            if not messagebox.askyesno("Внимание", "У приёма нет ни услуг, ни лекарств. Сумма будет 0. Провести?", parent=self):
                return

        total = self.db.calculate_appointment_total(record["appointment_id"])

        if not messagebox.askyesno("Подтверждение", f"Завершить приём и выставить счёт на {total} руб.?", parent=self):
            return

        try:
            self.db.update_appointment_status(record["appointment_id"], "завершён")

            self.db.create_payment_for_appointment(appointment_id=record["appointment_id"], client_id=record["client_id"], employee_id=record["employee_id"], amount=total)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        self.load_data()

class PaymentsTab(BaseTab):
    table_name = "Payments"
    pk_column = "payment_id"

    def __init__(self, parent, db):
        self.buttons = [("Принять оплату", self.accept_payment)]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_payments()

    def accept_payment(self):
        record = self._get_selected_record()
        if not record:
            return
        if record["status"] == "оплачен":
            messagebox.showwarning("Внимание", "Оплата уже принята", parent=self)
            return

        dlg = PaymentAcceptToplevel(
            self.winfo_toplevel(),
            self.db,
            payment=record,
            on_success=self.load_data,
        )
        self.wait_window(dlg)
 
class ClientsTab(BaseTab):
    table_name = "Clients"
    pk_column = "client_id"
    toplevel_class = ClientsToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать",         self.open_create),
            ("Редактировать",   self.open_edit),
            ("Удалить",         self.open_delete),
            ("Питомцы клиента", self.open_client_pets)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_clients()

    def open_client_pets(self):
        record = self._get_selected_record()
        if not record:
            return

        dlg = ClientPetsToplevel(
            self.winfo_toplevel(),
            self.db,
            client=record,
            on_success=self.load_data,
        )
        self.wait_window(dlg)

class PetsTab(BaseTab):
    table_name = "Pets"
    pk_column = "pet_id"
    toplevel_class = PetsToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_pets()

class EmployeesTab(BaseTab):
    table_name = "Employees"
    pk_column = "employee_id"
    toplevel_class = EmployeesToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_employees()
 
class BreedsTab(BaseTab):
    table_name = "Breeds"
    pk_column = "breed_id"
    toplevel_class = BreedsToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_breeds()

class SuppliersTab(BaseTab):
    table_name = "Suppliers"
    pk_column = "supplier_id"
    toplevel_class = SuppliersToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_suppliers()

class ServicesTab(BaseTab):
    table_name = "Services"
    pk_column = "service_id"
    toplevel_class = ServicesToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_services()

class MedicinesTab(BaseTab):
    table_name = "Medicines"
    pk_column = "medicine_id"
    toplevel_class = MedicinesToplevel

    def __init__(self, parent, db):
        self.buttons = [
            ("Создать", self.open_create),
            ("Редактировать", self.open_edit),
            ("Удалить", self.open_delete)
        ]
        super().__init__(parent, db)

    def fetch(self):
        return self.db.get_medicines()
        
class ReportsTab(ttk.Frame):
    REPORTS = {
        "revenue": {
            "title": "Выручка по дням",
            "method": "report_revenue_by_day",
            "keys":   ["day", "payments_count", "revenue"],
            "labels": ["Дата", "Оплат", "Выручка"],
        },
        "doctors": {
            "title": "Загрузка врачей",
            "method": "report_load_by_doctor",
            "keys":   ["employee", "appointments_count", "completed_count"],
            "labels": ["Врач", "Всего приёмов", "Завершено"],
        },
        "services": {
            "title": "Топ услуг",
            "method": "report_top_services",
            "keys":   ["name", "total_quantity", "total_revenue"],
            "labels": ["Услуга", "Кол-во", "Сумма"],
        },
        "debts": {
            "title": "Долги клиентов",
            "method": "report_unpaid_debts",
            "keys":   ["payment_id", "appointment_date", "client", "amount"],
            "labels": ["ID", "Дата приёма", "Клиент", "Сумма"],
        },
        "stock": {
            "title": "Остатки медикаментов",
            "method": "report_stock_balances",
            "keys":   ["name", "supplier", "stock", "unit"],
            "labels": ["Медикамент", "Поставщик", "Остаток", "Ед. изм."],
        },
    }

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db

        top = ttk.Frame(self, padding=10)
        top.pack(fill=X)

        ttk.Label(top, text="Отчёт:").pack(side=LEFT, padx=(0, 5))

        self.combo = ttk.Combobox(top, state="readonly", width=30, values=[r["title"] for r in self.REPORTS.values()])
        self.combo.pack(side=LEFT)
        self.combo.set(list(self.REPORTS.values())[0]["title"])
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        ttk.Button(top, text="Обновить", command=self.load_data).pack(side=LEFT, padx=10)

        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        self.summary = ttk.Label(self, text="", style="Total.TLabel")
        self.summary.pack(anchor=E, padx=10, pady=(0, 10))

        self.frame_tree = None
        self.tree = None

        self.load_data()

    def _current_report(self):
        title = self.combo.get()
        for key, r in self.REPORTS.items():
            if r["title"] == title:
                return r
        return None

    def load_data(self):
        report = self._current_report()
        if not report:
            return

        if self.frame_tree is not None:
            self.frame_tree.destroy()

        self.frame_tree, self.tree = treeview_with_scroll(self.tree_frame, keys=report["keys"], labels=report["labels"], height=18)
        self.frame_tree.pack(fill=BOTH, expand=True)

        try:
            rows = getattr(self.db, report["method"])()
        except Exception as e:
            print(e)
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        for row in rows:
            self.tree.insert("", "end", values=[row.get(k) or "—" for k in report["keys"]])

        self.summary.config(text=self._build_summary(report, rows))

    def _build_summary(self, report, rows):
        if report["method"] == "report_revenue_by_day":
            total = sum(r["revenue"] or 0 for r in rows)
            return f"Итого выручка: {total:.2f} руб."

        if report["method"] == "report_load_by_doctor":
            total = sum(r["appointments_count"] for r in rows)
            return f"Всего приёмов: {total}"

        if report["method"] == "report_top_services":
            total = sum(r["total_revenue"] or 0 for r in rows)
            return f"Топ-10 услуг на сумму: {total:.2f} руб."

        if report["method"] == "report_unpaid_debts":
            total = sum(r["amount"] or 0 for r in rows)
            return f"Общая задолженность: {total:.2f} руб."

        if report["method"] == "report_stock_balances":
            total = sum(r["stock"] or 0 for r in rows)
            return f"Всего позиций: {len(rows)}, общий остаток: {total} ед."

        return ""

class App(Tk):
    def __init__(self, db):
        super().__init__()
        apply_style(self)
        self.db = db
        self.title("АИС Ветеринарной клиники")
        self.geometry("1500x800")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=True, fill=BOTH)

        self.tabs.add(AppointmentsTab(self.tabs, self.db), text="Приёмы")
        self.tabs.add(PaymentsTab(self.tabs, self.db), text="Касса")
        self.tabs.add(ClientsTab(self.tabs, self.db), text="Клиенты")
        self.tabs.add(PetsTab(self.tabs, self.db), text="Питомцы")
        self.tabs.add(EmployeesTab(self.tabs, self.db), text="Сотрудники")
        self.tabs.add(BreedsTab(self.tabs, self.db), text="Породы")
        self.tabs.add(SuppliersTab(self.tabs, self.db), text="Поставщики")
        self.tabs.add(ServicesTab(self.tabs, self.db), text="Услуги")
        self.tabs.add(MedicinesTab(self.tabs, self.db), text="Медикаменты")
        self.tabs.add(ReportsTab(self.tabs, self.db), text="Отчёты")

        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_tab_changed(self, event):
        current = self.tabs.nametowidget(self.tabs.select())
        if hasattr(current, "load_data"):
            current.load_data()

    def run(self):
        self.mainloop()

    def on_close(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.destroy()

class Database:
    def __init__(self, host, port, dbname, user, password):
        self.connection = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, client_encoding="UTF8", cursor_factory=RealDictCursor)
        self.connection.autocommit = False

    def query(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(self, sql, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def insert(self, table, **fields):
        if not fields:
            raise ValueError("insert(): не переданы поля")
        columns = ", ".join(fields.keys())
        placeholders = ", ".join(["%s"] * len(fields))
        values = tuple(fields.values())
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(sql, values)

    def update(self, table, id_column, id_value, **fields):
        set_clause = ", ".join([f"{key} = %s" for key in fields.keys()])
        values = tuple(fields.values()) + (id_value,)
        sql = f"UPDATE {table} SET {set_clause} WHERE {id_column} = %s"
        self.execute(sql, values)

    def delete(self, table, id_column, id_value):
        sql = f"DELETE FROM {table} WHERE {id_column} = %s"
        self.execute(sql, (id_value,))

    def close(self):
        self.connection.close()

    def get_all(self, table, order_by="1"):
        return self.query(f"SELECT * FROM {table} ORDER BY {order_by}")

    def get_by_id(self, table, id_column, id_value):
        sql = f"SELECT * FROM {table} WHERE {id_column} = %s"
        rows = self.query(sql, (id_value,))
        return rows[0] if rows else None

    def get_appointments(self):
        sql = """
            SELECT
                appointment_id,
                Clients.surname || ' ' || Clients.name AS client,
                Pets.name AS pet,
                Employees.surname || ' ' || Employees.name AS employee,
                TO_CHAR(appointment_date, 'DD.MM.YYYY HH24:MI') AS appointment_date,
                status
            FROM Appointments
            LEFT JOIN Clients USING(client_id)
            LEFT JOIN Pets USING(pet_id)
            LEFT JOIN Employees USING(employee_id)
            ORDER BY
                CASE status
                    WHEN 'запланирован' THEN 1
                    WHEN 'завершён'     THEN 2
                    WHEN 'отменён'      THEN 3
                    ELSE 4
                END,
                appointment_date DESC
        """
        return self.query(sql)

    def get_appointment_services(self, appointment_id):
        sql = """
            SELECT
                Appointment_service.appointment_id,
                Appointment_service.service_id,
                Services.name,
                Appointment_service.quantity,
                Appointment_service.price
            FROM Appointment_service
            JOIN Services USING(service_id)
            WHERE Appointment_service.appointment_id = %s
        """
        return self.query(sql, (appointment_id,))

    def get_services_not_in_appointment(self, appointment_id):
        sql = """
            SELECT
                service_id,
                name
            FROM Services
            WHERE service_id NOT IN (
                SELECT service_id FROM Appointment_service WHERE appointment_id = %s
            )
            ORDER BY name
        """
        return self.query(sql, (appointment_id,))

    def remove_service_from_appointment(self, appointment_id, service_id):
        self.execute("DELETE FROM Appointment_service WHERE appointment_id = %s AND service_id = %s", (appointment_id, service_id))

    def get_appointment_medicines(self, appointment_id):
        sql = """
            SELECT
                Appointment_medicine.appointment_id,
                Appointment_medicine.medicine_id,
                Medicines.name,
                Appointment_medicine.quantity,
                Appointment_medicine.dosage,
                Appointment_medicine.price
            FROM Appointment_medicine
            JOIN Medicines USING(medicine_id)
            WHERE Appointment_medicine.appointment_id = %s
        """
        return self.query(sql, (appointment_id,))

    def get_medicines_not_in_appointment(self, appointment_id):
        sql = """
            SELECT medicine_id, name, price, stock
            FROM Medicines
            WHERE medicine_id NOT IN (
                SELECT medicine_id FROM Appointment_medicine WHERE appointment_id = %s
            )
            ORDER BY name
        """
        return self.query(sql, (appointment_id,))

    def remove_medicine_from_appointment(self, appointment_id, medicine_id):
        self.execute("DELETE FROM Appointment_medicine WHERE appointment_id = %s AND medicine_id = %s", (appointment_id, medicine_id))

    def get_payments(self):
        sql = """
            SELECT
                Payments.payment_id,
                TO_CHAR(Payments.payment_date, 'DD.MM.YYYY HH24:MI') AS payment_date,
                Employees.surname || ' ' || Employees.name AS employee,
                Clients.surname || ' ' || Clients.name AS client,
                Payments.payment_method,
                Payments.amount,
                Payments.status,
                Payments.appointment_id,
                TO_CHAR(Appointments.appointment_date, 'DD.MM.YYYY HH24:MI') AS appointment_date
            FROM Payments
            LEFT JOIN Employees ON Payments.employee_id = Employees.employee_id
            LEFT JOIN Clients ON Payments.client_id = Clients.client_id
            LEFT JOIN Appointments ON Payments.appointment_id = Appointments.appointment_id
            ORDER BY
                CASE Payments.status
                    WHEN 'не оплачен' THEN 1
                    WHEN 'оплачен' THEN 2
                    ELSE 3
                END,
                Payments.payment_date DESC
        """
        return self.query(sql)

    def get_clients(self):
        sql = """
            SELECT
                client_id,
                surname || ' ' || name || COALESCE(' ' || third_name, '') AS client,
                phone,
                email
            FROM Clients
            ORDER BY surname
        """
        return self.query(sql)

    def get_pets(self):
        sql = """
            SELECT
                pet_id,
                Pets.name,
                Breeds.pet_type AS pet_type,
                Breeds.name AS breed,
                gender,
                color,
                birth_date
            FROM Pets
            LEFT JOIN Breeds USING(breed_id)
            ORDER BY pet_type, Pets.name
        """
        return self.query(sql)

    def get_pets_by_client(self, client_id):
        sql = """
            SELECT
                Pets.pet_id,
                Pets.name,
                Breeds.pet_type AS pet_type,
                Breeds.name AS breed,
                gender,
                color,
                birth_date
            FROM Client_pet
            JOIN Pets USING(pet_id)
            LEFT JOIN Breeds USING(breed_id)
            WHERE Client_pet.client_id = %s
            ORDER BY Pets.name
        """
        return self.query(sql, (client_id,))

    def get_pets_not_by_client(self, client_id):
        sql = """
            SELECT
                Pets.pet_id,
                Pets.name || ' (' || COALESCE(Breeds.name, 'без породы') || ')' AS name
            FROM Pets
            LEFT JOIN Breeds USING(breed_id)
            WHERE Pets.pet_id NOT IN (
                SELECT pet_id FROM Client_pet WHERE client_id = %s
            )
            ORDER BY Pets.name
        """
        return self.query(sql, (client_id,))

    def get_employees(self):
        sql = """
            SELECT
                employee_id,
                surname || ' ' || name || COALESCE(' ' || third_name, '') AS employee,
                phone,
                email,
                role
            FROM Employees
            ORDER BY surname
        """
        return self.query(sql)

    def get_doctors(self):
        sql = """
            SELECT
                employee_id,
                surname || ' ' || name || COALESCE(' ' || third_name, '') AS employee
            FROM Employees
            WHERE role = 'doctor'
            ORDER BY surname
        """
        return self.query(sql)

    def get_receptionists(self):
        sql = """
            SELECT
                employee_id,
                surname || ' ' || name || COALESCE(' ' || third_name, '') AS employee
            FROM Employees
            WHERE role IN ('admin', 'receptionist')
            ORDER BY surname
        """
        return self.query(sql)

    def get_breeds(self):
        return self.get_all("Breeds", "pet_type, name")

    def get_suppliers(self):
        return self.get_all("Suppliers", "company_name")

    def get_services(self):
        return self.get_all("Services", "name")

    def get_medicines(self):
        sql = """
            SELECT
                medicine_id,
                Suppliers.company_name AS supplier,
                name,
                price,
                unit,
                stock
            FROM Medicines
            LEFT JOIN Suppliers USING(supplier_id)
            ORDER BY name
        """
        return self.query(sql)

    def get_medical_records(self, appointment_id):
        sql = """
            SELECT *
            FROM Medical_records
            WHERE appointment_id = %s
            ORDER BY created_at DESC
        """
        return self.query(sql, (appointment_id,))

    def link_pet_to_client(self, client_id, pet_id):
        self.insert("Client_pet", client_id=client_id, pet_id=pet_id)

    def unlink_pet_from_client(self, client_id, pet_id):
        self.execute("DELETE FROM Client_pet WHERE client_id = %s AND pet_id = %s", (client_id, pet_id))

    def update_appointment_status(self, appointment_id, status):
        self.execute("UPDATE Appointments SET status = %s WHERE appointment_id = %s", (status, appointment_id))

    def add_service_to_appointment(self, appointment_id, service_id, quantity):
        service = self.get_by_id("Services", "service_id", service_id)
        price = service["price"]
        self.insert("Appointment_service", appointment_id=appointment_id, service_id=service_id, quantity=quantity, price=price)

    def add_medicine_to_appointment(self, appointment_id, medicine_id, quantity, dosage):
        medicine = self.get_by_id("Medicines", "medicine_id", medicine_id)
        price = medicine["price"]
        self.insert("Appointment_medicine", appointment_id=appointment_id, medicine_id=medicine_id, quantity=quantity, dosage=dosage, price=price)

    def update_stock(self, medicine_id, delta):
        self.execute("UPDATE Medicines SET stock = stock + %s WHERE medicine_id = %s", (delta, medicine_id))

    def create_medical_record(self, appointment_id, reason, diagnosis, temperature, weight, recommendations, description):
        self.insert("Medical_records", appointment_id=appointment_id, reason=reason, diagnosis=diagnosis, temperature=temperature, weight=weight, recommendations=recommendations, description=description)

    def update_medical_record(self, record_id, reason, diagnosis, temperature, weight, recommendations, description):
        self.execute("""
            UPDATE Medical_records
            SET reason = %s,
                diagnosis = %s,
                temperature = %s,
                weight = %s,
                recommendations = %s,
                description = %s
            WHERE record_id = %s
        """, (reason, diagnosis, temperature, weight, recommendations, description, record_id))

    def calculate_appointment_total(self, appointment_id):
        sql = """
            SELECT
                COALESCE((
                    SELECT SUM(price * quantity)::float
                    FROM Appointment_service
                    WHERE appointment_id = %s
                ), 0)
                +
                COALESCE((
                    SELECT SUM(price * quantity)::float
                    FROM Appointment_medicine
                    WHERE appointment_id = %s
                ), 0)
                AS total
        """
        row = self.query(sql, (appointment_id, appointment_id))
        return row[0]["total"] if row else 0

    def create_payment_for_appointment(self, appointment_id, client_id, employee_id, amount):
        self.insert("Payments", appointment_id=appointment_id, client_id=client_id, employee_id=employee_id, amount=amount, status="не оплачен")

    def complete_payment(self, payment_id, client_id, employee_id, payment_method):
        self.execute("""
            UPDATE Payments
            SET status = %s,
                client_id = %s,
                employee_id = %s,
                payment_method = %s,
                payment_date = NOW()
            WHERE payment_id = %s
        """, ("оплачен", client_id, employee_id, payment_method, payment_id))

    def report_revenue_by_day(self):
        sql = """
            SELECT
                TO_CHAR(DATE(payment_date), 'DD.MM.YYYY') AS day,
                COUNT(*) AS payments_count,
                SUM(amount)::float AS revenue
            FROM Payments
            WHERE status = 'оплачен'
            GROUP BY DATE(payment_date)
            ORDER BY DATE(payment_date) DESC
        """
        return self.query(sql)

    def report_load_by_doctor(self):
        """Количество приёмов по врачам."""
        sql = """
            SELECT
                Employees.surname || ' ' || Employees.name AS employee,
                COUNT(*) AS appointments_count,
                SUM(CASE WHEN A.status = 'завершён' THEN 1 ELSE 0 END) AS completed_count
            FROM Appointments A
            JOIN Employees USING(employee_id)
            GROUP BY Employees.employee_id, Employees.surname, Employees.name
            ORDER BY appointments_count DESC
        """
        return self.query(sql)

    def report_top_services(self):
        """Топ услуг по количеству оказаний."""
        sql = """
            SELECT
                Services.name,
                SUM(Appointment_service.quantity) AS total_quantity,
                SUM(Appointment_service.price * Appointment_service.quantity)::float AS total_revenue
            FROM Appointment_service
            JOIN Services USING(service_id)
            GROUP BY Services.service_id, Services.name
            ORDER BY total_quantity DESC
            LIMIT 10
        """
        return self.query(sql)

    def report_unpaid_debts(self):
        """Неоплаченные счета (долги клиентов)."""
        sql = """
            SELECT
                Payments.payment_id,
                TO_CHAR(Appointments.appointment_date, 'DD.MM.YYYY HH24:MI') AS appointment_date,
                Clients.surname || ' ' || Clients.name AS client,
                Payments.amount
            FROM Payments
            LEFT JOIN Appointments ON Payments.appointment_id = Appointments.appointment_id
            LEFT JOIN Clients ON Payments.client_id = Clients.client_id
            WHERE Payments.status = 'не оплачен'
            ORDER BY Appointments.appointment_date DESC
        """
        return self.query(sql)

    def report_stock_balances(self):
        sql = """
            SELECT
                Medicines.name,
                Suppliers.company_name AS supplier,
                Medicines.stock,
                Medicines.unit
            FROM Medicines
            LEFT JOIN Suppliers USING(supplier_id)
            ORDER BY Medicines.stock ASC, Medicines.name
        """
        return self.query(sql)

if __name__ == "__main__":
    db_cfg = {
        "host": "localhost",
        "port": "5432", 
        "dbname": "vetclinic",
        "user": "postgres",
        "password": "1"
    }
    db = Database(**db_cfg)
    App(db).run()
