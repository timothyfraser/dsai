# app.py
# FDA Adverse Event Reporter — Shiny for Python (Core)
# Runs the openFDA Drug Event API query on user request and displays results.
# Pairs with LAB_your_good_api_query.md and FDA_good_query.python.py.

from datetime import datetime
from io import StringIO

from shiny import App, reactive, render, ui

from api_client import get_fda_events, get_api_key

# -----------------------------------------------------------------------------
# Custom styles
# -----------------------------------------------------------------------------

APP_CSS = """
.shiny-app .main-content { padding: 1.5rem 2rem; max-width: 1200px; }
.app-header { 
  background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%); 
  color: white; 
  padding: 1.25rem 1.5rem; 
  border-radius: 0.5rem; 
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(13, 110, 253, 0.25);
}
.app-header h2 { margin: 0; font-weight: 600; font-size: 1.5rem; }
.app-header p { margin: 0.35rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }
.stat-card { 
  background: white; 
  border-radius: 0.5rem; 
  padding: 1rem 1.25rem; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border: 1px solid #e9ecef;
}
.stat-card .stat-value { font-size: 1.5rem; font-weight: 700; color: #0d6efd; }
.stat-card .stat-label { font-size: 0.75rem; text-transform: uppercase; color: #6c757d; letter-spacing: 0.02em; }
.content-card { 
  background: white; 
  border-radius: 0.5rem; 
  padding: 1.25rem; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border: 1px solid #e9ecef;
  margin-bottom: 1rem;
}
.empty-state { 
  text-align: center; 
  padding: 2rem; 
  color: #6c757d; 
  background: #f8f9fa; 
  border-radius: 0.5rem;
  border: 1px dashed #dee2e6;
}
.sidebar-footer { font-size: 0.8rem; color: #6c757d; margin-top: 0.5rem; }
"""

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tags.div(
            ui.tags.p("Query parameters", class_="fw-semibold text-secondary small text-uppercase mb-2"),
            ui.input_numeric("limit", "Number of records", value=50, min=1, max=1000, step=10),
            ui.input_text("date_from", "Date from (YYYYMMDD)", value="20230101", placeholder="e.g. 20230101"),
            ui.input_text("date_to", "Date to (YYYYMMDD)", value="20241231", placeholder="e.g. 20241231"),
            ui.tags.div(
                ui.input_action_button("fetch_btn", "Fetch data", class_="btn-primary w-100"),
                class_="mt-3",
            ),
            ui.tags.hr(class_="my-3"),
            ui.input_action_button("clear_btn", "Clear results", class_="btn-outline-secondary w-100"),
            ui.tags.p(
                "Uses openFDA Drug Event API (FAERS). Add FDA_API_KEY in FDA.env for higher rate limits.",
                class_="sidebar-footer mt-3",
            ),
            class_="p-3",
        ),
        title=ui.tags.span("FDA Reporter", style="font-weight: 600;"),
        bg="#f8f9fa",
        width=280,
    ),
    ui.tags.div(
        ui.tags.style(APP_CSS),
        ui.tags.div(
            ui.tags.div(
                ui.tags.h2("Adverse Event Reports", class_="mb-1"),
                ui.tags.p(
                    "Query the FDA Adverse Event Reporting System (FAERS). Set parameters in the sidebar and click Fetch data.",
                    class_="mb-0 opacity-90",
                ),
                class_="app-header",
            ),
            class_="mb-4",
        ),
        ui.output_ui("summary_card"),
        ui.output_ui("table_card"),
        class_="main-content",
    ),
    title="FDA Adverse Event Reporter",
    fillable=True,
)

# -----------------------------------------------------------------------------
# Server
# -----------------------------------------------------------------------------


def server(input, output, session):
    query_result = reactive.value(None)
    is_loading = reactive.value(False)

    @reactive.effect
    @reactive.event(input.fetch_btn)
    def _fetch():
        is_loading.set(True)
        try:
            limit = input.limit()
            date_from = (input.date_from() or "").strip() or None
            date_to = (input.date_to() or "").strip() or None
            search_expr = None
            if date_from and date_to:
                search_expr = f"receivedate:[{date_from} TO {date_to}]"
            api_key = get_api_key() or None
            res = get_fda_events(limit=limit, search_expr=search_expr, api_key=api_key)
            if res.get("ok"):
                res = {**res, "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
            query_result.set(res)
        finally:
            is_loading.set(False)

    @reactive.effect
    @reactive.event(input.clear_btn)
    def _clear():
        query_result.set(None)

    def api_result():
        return query_result.get()

    @render.ui
    def summary_card():
        if is_loading.get():
            return ui.tags.div(
                ui.tags.div(
                    ui.tags.span("Loading...", class_="text-primary fw-medium"),
                    ui.tags.div(
                        ui.tags.div(class_="spinner-border spinner-border-sm text-primary", role="status"),
                        class_="mt-2",
                    ),
                    class_="empty-state",
                ),
                class_="content-card",
            )
        res = api_result()
        if res is None:
            return ui.tags.div(
                ui.tags.div(
                    ui.tags.p('Click "Fetch data" to load adverse event reports from the FDA.', class_="mb-0"),
                    ui.tags.p("Use the sidebar to set the number of records and optional date range.", class_="small mb-0 mt-1"),
                    class_="empty-state",
                ),
                class_="content-card",
            )
        if res["ok"]:
            meta = res.get("meta", {})
            results_info = meta.get("results", {})
            total = results_info.get("total", 0)
            n = len(res.get("results", []))
            fetched_at = res.get("fetched_at", "")
            return ui.tags.div(
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.span("Records returned", class_="stat-label"),
                        ui.tags.div(str(n), class_="stat-value"),
                        class_="stat-card me-3",
                        style="min-width: 120px;",
                    ),
                    ui.tags.div(
                        ui.tags.span("Total matching (API)", class_="stat-label"),
                        ui.tags.div(str(total), class_="stat-value", style="color: #495057 !important;"),
                        class_="stat-card me-3",
                        style="min-width: 140px;",
                    ),
                    ui.tags.div(
                        ui.tags.span("Fetched", class_="stat-label"),
                        ui.tags.div(fetched_at, class_="small", style="font-weight: 600; color: #495057;"),
                        class_="stat-card",
                        style="min-width: 160px;",
                    ),
                    class_="d-flex flex-wrap gap-2",
                ),
                ui.download_button("download_csv", "Download CSV", class_="btn btn-sm btn-outline-primary mt-2") if n > 0 else None,
                class_="content-card",
            )
        return ui.tags.div(
            ui.tags.div(
                ui.tags.strong("Error"),
                ui.tags.p(res.get("error", "Unknown error"), class_="text-danger mb-0 mt-1 small"),
                class_="content-card border border-danger",
            ),
        )

    @render.download(filename="fda_adverse_events.csv")
    def download_csv():
        res = api_result()
        if not res or not res.get("ok"):
            return
        df = res.get("df")
        if df is None or df.empty:
            return
        buf = StringIO()
        df.to_csv(buf, index=False)
        yield buf.getvalue()

    @render.ui
    def table_card():
        res = api_result()
        if res is None:
            return None
        if not res["ok"]:
            return None
        df = res.get("df")
        if df is None or df.empty:
            return ui.tags.div(
                ui.tags.div(
                    ui.tags.p("No records returned. Try a different date range or increase the limit.", class_="mb-0"),
                    class_="empty-state",
                ),
                class_="content-card",
            )
        n = len(df)
        return ui.tags.div(
            ui.tags.div(
                ui.tags.h5("Results", class_="mb-1"),
                ui.tags.span(f"({n} rows)", class_="text-muted small"),
                class_="d-flex align-items-baseline gap-2 mb-2",
            ),
            ui.output_data_frame("results_table"),
            class_="content-card",
        )

    @render.data_frame
    def results_table():
        res = api_result()
        if res is None or not res.get("ok"):
            return None
        df = res.get("df")
        if df is None or df.empty:
            return None
        return render.DataGrid(df, height="420px", width="100%", filters=True)

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------

app = App(app_ui, server)
