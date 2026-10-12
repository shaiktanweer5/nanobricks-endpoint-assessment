import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import webbrowser

from endpoint_agent import (
    build_endpoint_package,
    save_endpoint_package,
    save_html_report,
)


APP_TITLE = "Nanobricks Endpoint Assessment V3"

BG = "#f4f7f5"
CARD_BG = "#ffffff"

GREEN_DARK = "#14532d"
GREEN = "#1f7a3a"
GREEN_BRIGHT = "#2faf43"
GREEN_LIGHT = "#eaf7ed"

TEXT = "#20342a"
TEXT_MUTED = "#66756d"
BORDER = "#dfe8e2"

PASS_BG = "#e8f7ed"
PASS_TEXT = "#167b36"

REVIEW_BG = "#fff4d5"
REVIEW_TEXT = "#956900"

FAIL_BG = "#fde9e9"
FAIL_TEXT = "#b32626"


class EndpointAssessmentApp:
    def __init__(self, root):
        self.root = root

        self.root.title(
            APP_TITLE
        )

        self.root.geometry(
            "820x700"
        )

        self.root.minsize(
            700,
            540
        )

        self.root.configure(
            bg=BG
        )

        self.customer_var = tk.StringVar()

        self.technician_var = tk.StringVar(
            value="Nanobricks"
        )

        self.status_title_var = tk.StringVar(
            value="Ready"
        )

        self.status_message_var = tk.StringVar(
            value=(
                "Enter the customer details "
                "and start the endpoint assessment."
            )
        )

        self.pass_var = tk.StringVar(
            value="0"
        )

        self.review_var = tk.StringVar(
            value="0"
        )

        self.fail_var = tk.StringVar(
            value="0"
        )

        self.last_html_report = None

        self.build_ui()

        self.center_window()

    def center_window(self):
        self.root.update_idletasks()

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        x = int(
            (screen_width - width) / 2
        )

        y = int(
            (screen_height - height) / 2
        )

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def build_ui(self):
        self.build_header()

        self.build_scrollable_content()

        self.build_bottom_action_bar()

    def build_header(self):
        header = tk.Frame(
            self.root,
            bg=GREEN_DARK,
            height=145
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        inner = tk.Frame(
            header,
            bg=GREEN_DARK
        )

        inner.pack(
            fill="x",
            padx=42,
            pady=(25, 0)
        )

        brand = tk.Label(
            inner,
            text="NANOBRICKS",
            bg=GREEN_DARK,
            fg="#ccefd5",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        brand.pack(
            anchor="w"
        )

        title = tk.Label(
            inner,
            text="Endpoint Assessment",
            bg=GREEN_DARK,
            fg="white",
            font=(
                "Segoe UI",
                26,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            pady=(5, 0)
        )

        subtitle = tk.Label(
            inner,
            text=(
                "Windows health, readiness "
                "and security review • V3"
            ),
            bg=GREEN_DARK,
            fg="#d9efe0",
            font=(
                "Segoe UI",
                11
            )
        )

        subtitle.pack(
            anchor="w",
            pady=(4, 0)
        )

    def build_scrollable_content(self):
        wrapper = tk.Frame(
            self.root,
            bg=BG
        )

        wrapper.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            wrapper,
            bg=BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            wrapper,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scroll_frame = tk.Frame(
            self.canvas,
            bg=BG
        )

        self.scroll_window = (
            self.canvas.create_window(
                (0, 0),
                window=self.scroll_frame,
                anchor="nw"
            )
        )

        self.scroll_frame.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_scroll_frame
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self.mousewheel_scroll
        )

        content = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        content.pack(
            fill="both",
            expand=True,
            padx=38,
            pady=25
        )

        self.build_customer_card(
            content
        )

        self.build_run_button(
            content
        )

        self.build_status_card(
            content
        )

        self.build_summary_cards(
            content
        )

        footer_note = tk.Label(
            content,
            text=(
                "Local assessment • No document contents are read • "
                "Use only on authorized systems"
            ),
            bg=BG,
            fg="#859189",
            font=(
                "Segoe UI",
                8
            )
        )

        footer_note.pack(
            pady=(5, 20)
        )

    def update_scroll_region(
        self,
        event=None
    ):
        self.canvas.configure(
            scrollregion=
            self.canvas.bbox("all")
        )

    def resize_scroll_frame(
        self,
        event
    ):
        self.canvas.itemconfigure(
            self.scroll_window,
            width=event.width
        )

    def mousewheel_scroll(
        self,
        event
    ):
        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def build_customer_card(
        self,
        parent
    ):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            fill="x",
            pady=(0, 18)
        )

        inner = tk.Frame(
            card,
            bg=CARD_BG
        )

        inner.pack(
            fill="x",
            padx=25,
            pady=22
        )

        title = tk.Label(
            inner,
            text="Customer Details",
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                14,
                "bold"
            )
        )

        title.pack(
            anchor="w"
        )

        description = tk.Label(
            inner,
            text=(
                "These details will appear "
                "in the customer assessment report."
            ),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=(
                "Segoe UI",
                9
            )
        )

        description.pack(
            anchor="w",
            pady=(3, 18)
        )

        fields = tk.Frame(
            inner,
            bg=CARD_BG
        )

        fields.pack(
            fill="x"
        )

        left = tk.Frame(
            fields,
            bg=CARD_BG
        )

        left.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        right = tk.Frame(
            fields,
            bg=CARD_BG
        )

        right.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        customer_label = tk.Label(
            left,
            text="Customer / Company Name",
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        customer_label.pack(
            anchor="w",
            pady=(0, 7)
        )

        self.customer_entry = tk.Entry(
            left,
            textvariable=self.customer_var,
            font=(
                "Segoe UI",
                11
            ),
            bg="#fbfcfb",
            fg=TEXT,
            relief="solid",
            bd=1
        )

        self.customer_entry.pack(
            fill="x",
            ipady=8
        )

        technician_label = tk.Label(
            right,
            text="Technician / Assessor",
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        technician_label.pack(
            anchor="w",
            pady=(0, 7)
        )

        self.technician_entry = tk.Entry(
            right,
            textvariable=self.technician_var,
            font=(
                "Segoe UI",
                11
            ),
            bg="#fbfcfb",
            fg=TEXT,
            relief="solid",
            bd=1
        )

        self.technician_entry.pack(
            fill="x",
            ipady=8
        )

    def build_run_button(
        self,
        parent
    ):
        self.run_button = tk.Button(
            parent,
            text="▶  Run Endpoint Assessment",
            command=self.start_assessment,
            bg=GREEN_BRIGHT,
            fg="white",
            activebackground=GREEN,
            activeforeground="white",
            disabledforeground="#d7eadb",
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=13
        )

        self.run_button.pack(
            fill="x",
            pady=(0, 18)
        )

    def build_status_card(
        self,
        parent
    ):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            fill="x",
            pady=(0, 15)
        )

        inner = tk.Frame(
            card,
            bg=CARD_BG
        )

        inner.pack(
            fill="x",
            padx=22,
            pady=17
        )

        top = tk.Frame(
            inner,
            bg=CARD_BG
        )

        top.pack(
            fill="x"
        )

        self.status_dot = tk.Label(
            top,
            text="●",
            bg=CARD_BG,
            fg=GREEN_BRIGHT,
            font=(
                "Segoe UI",
                13,
                "bold"
            )
        )

        self.status_dot.pack(
            side="left"
        )

        status_title = tk.Label(
            top,
            textvariable=self.status_title_var,
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        )

        status_title.pack(
            side="left",
            padx=(8, 0)
        )

        status_message = tk.Label(
            inner,
            textvariable=self.status_message_var,
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=(
                "Segoe UI",
                9
            ),
            justify="left",
            anchor="w",
            wraplength=680
        )

        status_message.pack(
            fill="x",
            pady=(7, 0)
        )

    def build_summary_cards(
        self,
        parent
    ):
        summary = tk.Frame(
            parent,
            bg=BG
        )

        summary.pack(
            fill="x",
            pady=(0, 15)
        )

        self.create_summary_card(
            summary,
            "PASS",
            self.pass_var,
            PASS_BG,
            PASS_TEXT,
            0
        )

        self.create_summary_card(
            summary,
            "REVIEW",
            self.review_var,
            REVIEW_BG,
            REVIEW_TEXT,
            1
        )

        self.create_summary_card(
            summary,
            "FAIL",
            self.fail_var,
            FAIL_BG,
            FAIL_TEXT,
            2
        )

    def create_summary_card(
        self,
        parent,
        title,
        variable,
        background,
        foreground,
        column
    ):
        parent.grid_columnconfigure(
            column,
            weight=1
        )

        if column == 0:
            padx = (
                0,
                7
            )

        elif column == 1:
            padx = (
                7,
                7
            )

        else:
            padx = (
                7,
                0
            )

        card = tk.Frame(
            parent,
            bg=background
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=padx
        )

        number = tk.Label(
            card,
            textvariable=variable,
            bg=background,
            fg=foreground,
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        )

        number.pack(
            pady=(13, 0)
        )

        label = tk.Label(
            card,
            text=title,
            bg=background,
            fg=foreground,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        label.pack(
            pady=(0, 13)
        )

    def build_bottom_action_bar(self):
        action_bar = tk.Frame(
            self.root,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        action_bar.pack(
            fill="x",
            side="bottom"
        )

        inner = tk.Frame(
            action_bar,
            bg=CARD_BG
        )

        inner.pack(
            fill="x",
            padx=25,
            pady=13
        )

        self.open_report_button = tk.Button(
            inner,
            text="Open Customer HTML Report",
            command=self.open_report,
            state="disabled",
            bg=GREEN_DARK,
            fg="white",
            activebackground=GREEN,
            activeforeground="white",
            disabledforeground="#aebbb3",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10
        )

        self.open_report_button.pack(
            fill="x"
        )

    def start_assessment(self):
        customer = (
            self.customer_var
            .get()
            .strip()
        )

        technician = (
            self.technician_var
            .get()
            .strip()
            or "Nanobricks"
        )

        if not customer:
            messagebox.showwarning(
                "Customer Name Required",
                (
                    "Please enter the customer "
                    "or company name."
                )
            )

            self.customer_entry.focus_set()

            return

        self.run_button.config(
            state="disabled",
            text="Assessment Running..."
        )

        self.open_report_button.config(
            state="disabled"
        )

        self.status_title_var.set(
            "Assessment in progress"
        )

        self.status_message_var.set(
            (
                "Collecting system, security "
                "and readiness information..."
            )
        )

        self.status_dot.config(
            fg=REVIEW_TEXT
        )

        self.pass_var.set(
            "..."
        )

        self.review_var.set(
            "..."
        )

        self.fail_var.set(
            "..."
        )

        thread = threading.Thread(
            target=self.run_assessment,
            args=(
                customer,
                technician
            ),
            daemon=True
        )

        thread.start()

    def run_assessment(
        self,
        customer,
        technician
    ):
        try:
            package = (
                build_endpoint_package()
            )

            package[
                "assessment_context"
            ] = {
                "customer_name": customer,
                "technician_name": technician
            }

            json_file = (
                save_endpoint_package(
                    package
                )
            )

            html_file = (
                save_html_report(
                    package
                )
            )

            self.last_html_report = Path(
                html_file
            )

            summary = package.get(
                "summary",
                {}
            )

            self.root.after(
                0,
                self.assessment_complete,
                summary,
                json_file,
                html_file
            )

        except Exception as exc:
            self.root.after(
                0,
                self.assessment_failed,
                str(exc)
            )

    def assessment_complete(
        self,
        summary,
        json_file,
        html_file
    ):
        pass_count = summary.get(
            "pass",
            0
        )

        review_count = summary.get(
            "review",
            0
        )

        fail_count = summary.get(
            "fail",
            0
        )

        self.pass_var.set(
            str(pass_count)
        )

        self.review_var.set(
            str(review_count)
        )

        self.fail_var.set(
            str(fail_count)
        )

        self.status_title_var.set(
            "Assessment completed"
        )

        self.status_message_var.set(
            (
                "Report generated successfully. "
                f"JSON: {json_file.name} • "
                f"HTML: {html_file.name}"
            )
        )

        self.status_dot.config(
            fg=GREEN_BRIGHT
        )

        self.run_button.config(
            state="normal",
            text="↻  Run Assessment Again"
        )

        self.open_report_button.config(
            state="normal"
        )

        messagebox.showinfo(
            "Assessment Complete",
            (
                "Nanobricks endpoint assessment "
                "completed successfully."
            )
        )

    def assessment_failed(
        self,
        error_message
    ):
        self.pass_var.set(
            "0"
        )

        self.review_var.set(
            "0"
        )

        self.fail_var.set(
            "0"
        )

        self.status_title_var.set(
            "Assessment failed"
        )

        self.status_message_var.set(
            error_message
        )

        self.status_dot.config(
            fg=FAIL_TEXT
        )

        self.run_button.config(
            state="normal",
            text="▶  Run Endpoint Assessment"
        )

        self.open_report_button.config(
            state="disabled"
        )

        messagebox.showerror(
            "Assessment Failed",
            error_message
        )

    def open_report(self):
        if (
            not self.last_html_report
            or not self.last_html_report.exists()
        ):
            messagebox.showwarning(
                "Report Not Found",
                (
                    "No HTML report "
                    "is available yet."
                )
            )

            return

        webbrowser.open(
            self.last_html_report
            .resolve()
            .as_uri()
        )


def main():
    root = tk.Tk()

    EndpointAssessmentApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()