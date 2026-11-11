
import streamlit as st
import pandas as pd
import plotly.express as px
import model


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MacroLab | Central Bank Governor",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 MacroLab")
st.subheader("Can You Beat the Taylor Rule?")
st.caption("A 24-quarter central bank governor simulation")

st.markdown("""
You are the central bank governor. Set monetary policy,
forecast inflation, and compete against an automatic
Taylor Rule benchmark.
""")


# ============================================================
# 2. INITIALISE GAME
# ============================================================

def initialise_game():

    demand_shocks, supply_shocks = model.generate_shocks()

    st.session_state.human_state = model.create_initial_state()
    st.session_state.taylor_state = model.create_initial_state()

    st.session_state.demand_shocks = demand_shocks
    st.session_state.supply_shocks = supply_shocks

    st.session_state.results = []
    st.session_state.game_step = 0
    st.session_state.game_over = False


if "game_step" not in st.session_state:
    initialise_game()


# ============================================================
# 3. CURRENT GAME STATUS
# ============================================================

game_step = st.session_state.game_step

if game_step < model.GAME_QUARTERS:

    human_state = st.session_state.human_state

    current_inflation = human_state["inflation"][-1]
    current_output = human_state["output_gap"][-1]

    quarter = model.INITIAL_QUARTERS + game_step + 1

    st.progress(
        game_step / model.GAME_QUARTERS,
        text=f"Quarter {quarter} of {model.TOTAL_QUARTERS}"
    )

    st.divider()

    # ========================================================
    # 4. ECONOMIC INDICATORS
    # ========================================================

    st.header("Your Economy")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Current Inflation",
        f"{current_inflation:.2f}%"
    )

    col2.metric(
        "Output Gap",
        f"{current_output:.2f}%"
    )

    col3.metric(
        "Inflation Target",
        f"{model.PI_TARGET:.2f}%"
    )

    st.divider()

    # ========================================================
    # 5. HUMAN GOVERNOR DECISION
    # ========================================================

    st.header("Your Monetary Policy Decision")

    with st.form("policy_form"):

        human_rate = st.slider(
            "Set your policy interest rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=0.25
        )

        human_forecast = st.number_input(
            "Forecast next-quarter inflation (%)",
            min_value=0.0,
            max_value=30.0,
            value=3.0,
            step=0.1
        )

        submitted = st.form_submit_button(
            "Submit Policy Decision",
            use_container_width=True
        )

    # ========================================================
    # 6. PROCESS THE QUARTER
    # ========================================================

    if submitted:

        taylor_state = st.session_state.taylor_state

        # Taylor Rule benchmark decision

        taylor_rate = model.taylor_rule(
            taylor_state["inflation"][-1],
            taylor_state["output_gap"][-1]
        )

        # Common economic shocks

        demand_shock = st.session_state.demand_shocks[game_step]
        supply_shock = st.session_state.supply_shocks[game_step]

        # Update human economy

        human_new_inflation, human_new_output = model.update_economy(
            st.session_state.human_state,
            human_rate,
            demand_shock,
            supply_shock
        )

        # Update Taylor Rule economy

        taylor_new_inflation, taylor_new_output = model.update_economy(
            st.session_state.taylor_state,
            taylor_rate,
            demand_shock,
            supply_shock
        )

        # Inflation forecast accuracy

        forecast_error = human_forecast - human_new_inflation

        # Store quarterly results

        st.session_state.results.append({

            "Quarter": quarter,

            "Human Interest Rate": human_rate,
            "Taylor Interest Rate": taylor_rate,

            "Human Inflation": human_new_inflation,
            "Taylor Inflation": taylor_new_inflation,

            "Human Output Gap": human_new_output,
            "Taylor Output Gap": taylor_new_output,

            "Human Inflation Forecast": human_forecast,
            "Forecast Error": forecast_error,

            "Demand Shock": demand_shock,
            "Supply Shock": supply_shock

        })

        st.session_state.game_step += 1

        st.rerun()


# ============================================================
# 7. QUARTERLY RESULTS
# ============================================================

if st.session_state.results:

    st.divider()
    st.header("Quarterly Results")

    results_df = pd.DataFrame(st.session_state.results)

    st.dataframe(
        results_df.tail(5).round(3),
        use_container_width=True
    )


# ============================================================
# 8. FINAL RESULTS AND SCORING
# ============================================================

if st.session_state.game_step >= model.GAME_QUARTERS:

    st.session_state.game_over = True

    df = pd.DataFrame(st.session_state.results)

    st.divider()
    st.header("🏆 Final Governor Performance")

    human_pi_loss, human_y_loss, human_loss = model.central_bank_loss(
        df["Human Inflation"].to_numpy(),
        df["Human Output Gap"].to_numpy()
    )

    taylor_pi_loss, taylor_y_loss, taylor_loss = model.central_bank_loss(
        df["Taylor Inflation"].to_numpy(),
        df["Taylor Output Gap"].to_numpy()
    )

    human_forecast_mse = (df["Forecast Error"] ** 2).mean()
    human_forecast_rmse = human_forecast_mse ** 0.5

    score_table = pd.DataFrame({

        "Performance Measure": [
            "Inflation Loss",
            "Output Gap Loss",
            "Total Central Bank Loss",
            "Inflation Forecast MSE",
            "Inflation Forecast RMSE"
        ],

        "Human Governor": [
            human_pi_loss,
            human_y_loss,
            human_loss,
            human_forecast_mse,
            human_forecast_rmse
        ],

        "Taylor Rule Governor": [
            taylor_pi_loss,
            taylor_y_loss,
            taylor_loss,
            None,
            None
        ]

    })

    st.dataframe(
        score_table.round(4),
        use_container_width=True
    )

    # Winner declaration

    if human_loss < taylor_loss:
        st.success("🏆 HUMAN GOVERNOR WINS!")

    elif taylor_loss < human_loss:
        st.error("TAYLOR RULE GOVERNOR WINS!")

    else:
        st.info("IT IS A DRAW!")

    # ========================================================
    # 9. INFLATION COMPARISON
    # ========================================================

    st.subheader("Inflation Stability")

    fig1 = px.line(
        df,
        x="Quarter",
        y=["Human Inflation", "Taylor Inflation"],
        markers=True,
        title="Human Governor vs Taylor Rule"
    )

    fig1.add_hline(
        y=model.PI_TARGET,
        line_dash="dash",
        annotation_text="Inflation Target"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # ========================================================
    # 10. OUTPUT GAP COMPARISON
    # ========================================================

    st.subheader("Output Gap Comparison")

    fig2 = px.line(
        df,
        x="Quarter",
        y=["Human Output Gap", "Taylor Output Gap"],
        markers=True
    )

    fig2.add_hline(
        y=0,
        line_dash="dash",
        annotation_text="Potential Output"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ========================================================
    # 11. INTEREST RATE COMPARISON
    # ========================================================

    st.subheader("Monetary Policy Rate Comparison")

    fig3 = px.line(
        df,
        x="Quarter",
        y=["Human Interest Rate", "Taylor Interest Rate"],
        markers=True
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ========================================================
    # 12. FORECAST ACCURACY
    # ========================================================

    st.subheader("Inflation Forecast vs Actual Inflation")

    fig4 = px.line(
        df,
        x="Quarter",
        y=["Human Inflation Forecast", "Human Inflation"],
        markers=True
    )

    st.plotly_chart(fig4, use_container_width=True)

    # ========================================================
    # 13. DOWNLOAD RESULTS
    # ========================================================

    st.subheader("Download Simulation Results")

    st.download_button(
        "Download Game Results",
        df.to_csv(index=False),
        file_name="governor_game_results.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download Score Table",
        score_table.to_csv(index=False),
        file_name="governor_game_scores.csv",
        mime="text/csv"
    )

    if st.button("Start a New Game"):
        initialise_game()
        st.rerun()


# ============================================================
# 14. RESTART GAME
# ============================================================

if not st.session_state.game_over:

    if st.button("Restart Game"):
        initialise_game()
        st.rerun()

