
# ============================================================
# CAN YOU BEAT THE TAYLOR RULE?
# MACROLAB ECONOMIC SIMULATION ENGINE
#
# Original Jupyter model transferred into model.py
# ============================================================

import numpy as np


# ============================================================
# 1. MODEL PARAMETERS
# ============================================================

R_STAR = 2.0
PI_TARGET = 2.0

ALPHA = 0.5
BETA = 0.5

# IS curve coefficients: Rudebusch-Svensson (1999)
IS_A1 = 1.16
IS_A2 = -0.25
IS_BETA = 0.10

# Phillips curve coefficients: Rudebusch-Svensson (1999)
PC_A1 = 0.70
PC_A2 = -0.10
PC_A3 = 0.28
PC_A4 = 0.12
PC_BETA = 0.14

# Illustrative reference means for deviations
PI_MEAN = 2.0
INTEREST_MEAN = 4.0

# Game duration
TOTAL_QUARTERS = 24
INITIAL_QUARTERS = 4
GAME_QUARTERS = 20

# Central bank loss-function parameter
LAMBDA = 0.5

# Initial economic conditions
INITIAL_INFLATION = 4.5
INITIAL_OUTPUT_GAP = -1.2
INITIAL_INTEREST_RATE = 5.0


# ============================================================
# 2. INITIAL ECONOMIC CONDITIONS
# ============================================================

def create_initial_state():

    return {
        "inflation": [INITIAL_INFLATION] * 4,
        "output_gap": [INITIAL_OUTPUT_GAP] * 4,
        "interest_rate": [INITIAL_INTEREST_RATE] * 4
    }


# ============================================================
# 3. TAYLOR RULE
# ============================================================

def taylor_rule(inflation, output_gap):

    interest_rate = (
        R_STAR
        + inflation
        + ALPHA * (inflation - PI_TARGET)
        + BETA * output_gap
    )

    return interest_rate


# ============================================================
# 4. RUDEBUSCH-SVENSSON IS CURVE
# ============================================================

def is_curve(state, current_interest_rate, demand_shock):

    y_t = state["output_gap"][-1]
    y_previous = state["output_gap"][-2]

    # Four-quarter nominal interest-rate average
    # expressed as deviations from the reference mean

    interest_history = [
        value - INTEREST_MEAN
        for value in state["interest_rate"][-3:]
    ]

    interest_history.append(
        current_interest_rate - INTEREST_MEAN
    )

    # Four-quarter inflation average
    # expressed as deviations from the reference mean

    inflation_history = [
        value - PI_MEAN
        for value in state["inflation"][-4:]
    ]

    average_interest = np.mean(interest_history)
    average_inflation = np.mean(inflation_history)

    # Published IS curve structure

    y_next = (
        IS_A1 * y_t
        + IS_A2 * y_previous
        - IS_BETA * (
            average_interest - average_inflation
        )
        + demand_shock
    )

    return y_next


# ============================================================
# 5. RUDEBUSCH-SVENSSON PHILLIPS CURVE
# ============================================================

def phillips_curve(state, current_output_gap, supply_shock):

    # Inflation observations converted into deviations

    inflation_history = [
        value - PI_MEAN
        for value in state["inflation"][-4:]
    ]

    pi_t = inflation_history[-1]
    pi_t_minus_1 = inflation_history[-2]
    pi_t_minus_2 = inflation_history[-3]
    pi_t_minus_3 = inflation_history[-4]

    # Published Phillips curve structure

    inflation_deviation_next = (
        PC_A1 * pi_t
        + PC_A2 * pi_t_minus_1
        + PC_A3 * pi_t_minus_2
        + PC_A4 * pi_t_minus_3
        + PC_BETA * current_output_gap
        + supply_shock
    )

    # Convert deviation into inflation level

    inflation_next = (
        PI_MEAN + inflation_deviation_next
    )

    return inflation_next


# ============================================================
# 6. SHOCK GENERATOR
# ============================================================

def generate_shocks():

    rng = np.random.default_rng(42)

    demand_shocks = rng.normal(
        loc=0.0,
        scale=0.30,
        size=GAME_QUARTERS
    )

    supply_shocks = rng.normal(
        loc=0.0,
        scale=0.20,
        size=GAME_QUARTERS
    )

    return demand_shocks, supply_shocks


# ============================================================
# 7. ECONOMIC STATE UPDATE
# ============================================================

def update_economy(
    state,
    interest_rate,
    demand_shock,
    supply_shock
):

    # Current output gap
    current_output_gap = state["output_gap"][-1]

    # Calculate next output gap
    new_output_gap = is_curve(
        state,
        interest_rate,
        demand_shock
    )

    # Phillips curve uses CURRENT output gap
    # to calculate NEXT QUARTER inflation

    new_inflation = phillips_curve(
        state,
        current_output_gap,
        supply_shock
    )

    # Update economic histories

    state["interest_rate"].append(interest_rate)
    state["output_gap"].append(new_output_gap)
    state["inflation"].append(new_inflation)

    return new_inflation, new_output_gap


# ============================================================
# 8. CENTRAL BANK QUADRATIC LOSS FUNCTION
# ============================================================

def central_bank_loss(
    inflation,
    output_gap,
    inflation_target=PI_TARGET,
    lam=LAMBDA
):

    inflation_loss = np.mean(
        (np.asarray(inflation) - inflation_target) ** 2
    )

    output_loss = np.mean(
        np.asarray(output_gap) ** 2
    )

    total_loss = (
        inflation_loss
        + lam * output_loss
    )

    return inflation_loss, output_loss, total_loss

