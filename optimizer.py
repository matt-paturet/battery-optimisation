import numpy as np
from scipy.optimize import minimize


def run(capacity: float = 1.0,
        volume: float = 1.0,
        efficiency: float = 0.9,
        input_soc: float = 0.5,
        prices: np.array = None,
        charge_cost: float = 5.0,
        discharge_cost: float = 5.0,
        activation: float = 5.0,
        time_frequency: float = 0.5,
        final_soc: float = 0.5):
    """
    Perform an optimization for battery dispatch for a given price vector.
    :param capacity: Battery power in MW
    :param volume: Battery volume in MWh (ie a 1MW/2MWh battery would take 2h to fully charge from 0%)
    :param efficiency: Round trip efficiency in %
    :param input_soc: Starting point for state of charge in %
    :param prices: Price vector
    :param charge_cost: Cost to charge battery
    :param discharge_cost: Cost to discharge battery
    :param activation: Activation spread between charging and discharging
    :param time_frequency: Time frequency of price data in hours (30min=0.5, 60min=1)
    :param final_soc: Ending point for state of charge in %
    :return: Charge profile, discharge profile, SoC, algorithm solution
    """

    # Time period for optimization
    period = len(prices)

    # Define cost vector
    charge_cost = np.full(period, charge_cost)
    discharge_cost = np.full(period, discharge_cost)
    activation = np.full(period, activation)

    # Define constants
    mw_to_mwh = time_frequency
    steps_full_trip = (volume / capacity) * (1 / time_frequency)
    soc_step = np.full(period, (volume / capacity) * (1 / steps_full_trip))

    # Initialize decision variables vector (charge profile, discharge profile & SoC)
    x0 = np.zeros(period * 3)
    charge_idx = slice(0, period)
    discharge_idx = slice(period, period * 2)
    soc_idx = slice(period * 2, period * 3)

    # Initilalize bounds vector for decision variables
    charge_bounds = [(0.0, capacity)] * period
    discharge_bounds = [(0.0, capacity)] * period
    soc_bounds = [(0.0, volume)] * period
    all_bounds = charge_bounds + discharge_bounds + soc_bounds

    # Define objective function
    def objective(x, p):
        charge = x[charge_idx]
        discharge = x[discharge_idx]
        return sum(
            (charge * mw_to_mwh * efficiency) * (p + charge_cost)
        ) - sum(
            discharge * mw_to_mwh * (p - discharge_cost - activation)
        )

    # Define constraints
    def soc_change(x):
        charge = x[charge_idx]
        discharge = x[discharge_idx]
        soc = x[soc_idx]
        return np.array(
            soc[1:] - soc[:-1]
            - charge[:-1] * efficiency * soc_step[:-1]
            + discharge[:-1] * soc_step[:-1]
        )

    def start_soc(x):
        soc = x[soc_idx]
        return soc[0] - input_soc

    def end_soc(x):
        soc = x[soc_idx]
        return soc[-1] - final_soc

    def no_final_discharge(x):
        discharge = x[discharge_idx]
        return discharge[-1]

    constraints = [
        {'type': 'eq', 'fun': soc_change},
        {'type': 'eq', 'fun': start_soc},
        {'type': 'eq', 'fun': end_soc},
        {'type': 'eq', 'fun': no_final_discharge}
    ]

    sol = minimize(
        objective,
        x0,
        args=(prices,),
        method='SLSQP',
        bounds=all_bounds,
        constraints=constraints
    )

    obj = sol.fun
    charge = sol.x[charge_idx]
    discharge = sol.x[discharge_idx]
    soc = (sol.x[soc_idx] / volume)

    return charge, discharge, soc, sol
