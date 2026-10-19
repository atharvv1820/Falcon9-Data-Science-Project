
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

DATA_PATH = "/content/spacex_data/spacex_launch_dash.csv"

df = pd.read_csv(DATA_PATH)

# Validate and clean required columns
required = [
    "Flight Number", "Launch Site", "class", "Payload Mass (kg)",
    "Booster Version"
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["class"] = pd.to_numeric(df["class"], errors="coerce")
df["Payload Mass (kg)"] = pd.to_numeric(
    df["Payload Mass (kg)"], errors="coerce"
)
df["Flight Number"] = pd.to_numeric(
    df["Flight Number"], errors="coerce"
)
df = df.dropna(subset=["class", "Payload Mass (kg)", "Flight Number"])
df["class"] = df["class"].astype(int)

sites = sorted(df["Launch Site"].dropna().unique())
max_payload = int(df["Payload Mass (kg)"].max())
max_payload = max(1000, ((max_payload + 999) // 1000) * 1000)

app = Dash(
    __name__,
    serve_locally=True
)

# Serve Plotly.js from the installed Plotly package
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


app.layout = html.Div([
    html.H1(
        "SpaceX Falcon 9 Launch Dashboard",
        style={"textAlign": "center"}
    ),

    html.Label("Select Launch Site:"),
    dcc.Dropdown(
        id="site-dropdown",
        options=[{"label": "All Sites", "value": "ALL"}]
                + [{"label": s, "value": s} for s in sites],
        value="ALL",
        clearable=False
    ),

    html.Br(),
    html.Label("Select Payload Mass Range (kg):"),
    dcc.RangeSlider(
        id="payload-slider",
        min=0,
        max=max_payload,
        step=500,
        value=[0, max_payload],
        marks={
            i: str(i)
            for i in range(0, max_payload + 1, max(1000, max_payload // 5))
        },
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Div(id="filtered-count", style={"marginTop": "20px"}),

    dcc.Graph(id="success-pie-chart"),
    dcc.Graph(id="payload-scatter-chart")
], style={"maxWidth": "1100px", "margin": "auto", "padding": "20px"})


@app.callback(
    Output("success-pie-chart", "figure"),
    Output("payload-scatter-chart", "figure"),
    Output("filtered-count", "children"),
    Input("site-dropdown", "value"),
    Input("payload-slider", "value")
)
def update_dashboard(selected_site, payload_range):
    filtered = df[
        df["Payload Mass (kg)"].between(
            payload_range[0], payload_range[1], inclusive="both"
        )
    ].copy()

    if selected_site != "ALL":
        filtered = filtered[filtered["Launch Site"] == selected_site]

    if filtered.empty:
        empty = px.scatter(title="No launches match these filters")
        return empty, empty, "No matching launches."

    filtered["Landing Result"] = filtered["class"].map({
        1: "Successful landing",
        0: "Unsuccessful landing"
    }).fillna("Unknown")

    pie_data = (
        filtered["Landing Result"]
        .value_counts()
        .rename_axis("Landing Result")
        .reset_index(name="Launch Count")
    )

    pie_fig = px.pie(
        pie_data,
        names="Landing Result",
        values="Launch Count",
        title="Landing Outcomes"
    )
    pie_fig.update_layout(legend_title_text="Landing Result")

    scatter_fig = px.scatter(
        filtered,
        x="Flight Number",
        y="Payload Mass (kg)",
        color="Landing Result",
        hover_data=["Launch Site", "Booster Version"],
        title="Payload Mass vs. Flight Number"
    )

    scatter_fig.update_layout(
        xaxis_title="Flight Number",
        yaxis_title="Payload Mass (kg)"
    )

    message = f"Showing {len(filtered)} launches."
    return pie_fig, scatter_fig, message


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
