"""
Core simulation engine: runs a single 100-quarter (25-year) simulation
for the Suao retirement community project.
"""

import numpy as np
from .parameters import (
    AGE_MORTALITY_TABLE, AGE_CARE_TRANSFER_TABLE,
    ANNUAL_VOLUNTARY_EXIT_RATE, REVENUE_STREAM_OPTIONS,
    BRAND_AGING_OPTIONS,
)


def _lookup_rate(age, table, default_key=None):
    """Interpolate from age-rate table."""
    keys = sorted(table.keys())
    if age <= keys[0]:
        return table[keys[0]]
    if age >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= age < keys[i + 1]:
            frac = (age - keys[i]) / (keys[i + 1] - keys[i])
            return table[keys[i]] * (1 - frac) + table[keys[i + 1]] * frac
    return table[keys[-1]]


class PhaseState:
    """Tracks a single development phase."""

    def __init__(self, phase_id, total_units, start_quarter):
        self.phase_id = phase_id
        self.total_units = total_units
        self.start_quarter = start_quarter
        self.occupied = 0
        self.resident_ages = []  # list of current ages
        self.activated = False
        self.construction_done = False
        self.construction_quarters = 8  # 2 years to build

    @property
    def occupancy_rate(self):
        if self.total_units == 0:
            return 0.0
        return self.occupied / self.total_units

    @property
    def available_units(self):
        if not self.construction_done:
            return 0
        return max(0, self.total_units - self.occupied)


class SimulationResult:
    """Stores the full trajectory of a single simulation run."""

    def __init__(self, n_quarters=100):
        self.n_quarters = n_quarters

        # Per-quarter time series
        self.total_occupied = np.zeros(n_quarters)
        self.total_units_active = np.zeros(n_quarters)
        self.occupancy_rate = np.zeros(n_quarters)

        # Financial
        self.deposit_trust_pool = np.zeros(n_quarters)
        self.operating_cashflow = np.zeros(n_quarters)
        self.capex_reserve = np.zeros(n_quarters)
        self.emergency_reserve = np.zeros(n_quarters)
        self.cumulative_cashflow = np.zeros(n_quarters)
        self.quarterly_revenue = np.zeros(n_quarters)
        self.quarterly_cost = np.zeros(n_quarters)
        self.quarterly_net = np.zeros(n_quarters)

        # Brand & operations
        self.brand_trust = np.zeros(n_quarters)
        self.brand_vitality = np.zeros(n_quarters)
        self.operational_capability = np.zeros(n_quarters)
        self.median_age = np.zeros(n_quarters)
        self.pct_over_80 = np.zeros(n_quarters)

        # Market
        self.market_pool_remaining = np.zeros(n_quarters)
        self.cultural_acceptance = np.zeros(n_quarters)
        self.macro_factor = np.zeros(n_quarters)

        # Phase tracking
        self.phase_activations = {}  # phase_id -> quarter activated
        self.phase_occupancy = {}    # phase_id -> array[n_quarters]

        # Rules
        self.rules_status = np.zeros((n_quarters, 10), dtype=int)  # 0=green,1=yellow,2=red

        # New move-ins per quarter
        self.new_move_ins = np.zeros(n_quarters)
        self.exits = np.zeros(n_quarters)

        # Refund tracking
        self.refund_due = np.zeros(n_quarters)
        self.refund_paid = np.zeros(n_quarters)
        self.refund_backlog = np.zeros(n_quarters)

        # Cashflow breakdown (for waterfall chart)
        self.cf_deposit_income = np.zeros(n_quarters)
        self.cf_monthly_fee = np.zeros(n_quarters)
        self.cf_other_revenue = np.zeros(n_quarters)
        self.cf_construction = np.zeros(n_quarters)
        self.cf_operating = np.zeros(n_quarters)
        self.cf_refund = np.zeros(n_quarters)
        self.cf_capital_cost = np.zeros(n_quarters)

        # Stress test info
        self.stress_name = None
        self.failed_quarter = -1  # quarter where funds went negative


def run_simulation(params, rng=None, stress_scenario=None):
    """
    Run a single 100-quarter simulation.

    Args:
        params: dict of all parameters
        rng: numpy RandomState for stochastic elements
        stress_scenario: optional stress test overrides

    Returns:
        SimulationResult
    """
    if rng is None:
        rng = np.random.RandomState()

    N_Q = 100
    result = SimulationResult(N_Q)

    # --- Initialize phases ---
    phases = []
    for i in range(params['total_phases']):
        p = PhaseState(i, params['phase_units'][i], start_quarter=-1)
        result.phase_occupancy[i] = np.zeros(N_Q)
        phases.append(p)

    # Phase 0 starts at t=0, pre-built (construction already done)
    phases[0].activated = True
    phases[0].start_quarter = 0
    phases[0].construction_done = True
    result.phase_activations[0] = 0

    # --- Initialize stocks ---
    brand_trust = float(params['initial_brand_trust'])
    operational_capability = float(params.get('operational_capability_init', 20))
    cultural_acceptance = float(params['initial_cultural_acceptance'])
    macro = 1.0
    recession_remaining = 0
    market_pool = float(params['target_pool'])
    initial_pool = float(params['target_pool'])

    # Financial pools - initialize with total budget
    total_budget = float(params['total_budget'])
    # Construction cost per unit (rough: budget / total units)
    cost_per_unit = total_budget / sum(params['phase_units'])
    # Phase 0 construction cost
    phase0_cost = phases[0].total_units * cost_per_unit
    total_invested = phase0_cost  # track how much capital has been deployed

    deposit_pool = 0.0
    operating_cash = total_budget * 0.15  # 15% as initial operating reserve
    capex_reserve = total_budget * 0.25 - phase0_cost  # 25% for capex, minus phase 0
    emergency_reserve = total_budget * 0.05  # 5% emergency
    cumulative_cf = -(phase0_cost + operating_cash + capex_reserve + emergency_reserve)
    refund_backlog = 0.0
    consecutive_illiquid = 0  # P1: 連續流動性不足的季數

    # Revenue streams active quarters tracker
    revenue_stream_start = {}

    # Brand aging countermeasures
    countermeasures = params.get('brand_aging_countermeasures', [])
    total_decay_reduction = min(0.70, sum(
        BRAND_AGING_OPTIONS.get(c, {}).get('decay_reduction', 0)
        for c in countermeasures
    ))

    # Medical boost
    medical_boost = 1.0
    if params['medical_integration'] == 2:
        medical_boost = 1.15
    elif params['medical_integration'] == 3:
        medical_boost = 1.30

    # Onsen boost
    onsen_boost_val = 0.0
    if params.get('onsen_level', 0) == 1:
        onsen_boost_val = 0.10
    elif params.get('onsen_level', 0) == 2:
        onsen_boost_val = 0.20

    # Cost inflation tracker (for stress tests)
    cost_inflation_accum = 1.0

    # ==================== MAIN LOOP ====================
    for t in range(N_Q):
        year = t / 4

        # --- Stress scenario overrides ---
        stress_macro = 1.0
        stress_exit_extra = 0.0
        stress_zero_movin = False
        stress_cost_inf = 0.0

        if stress_scenario:
            sq = stress_scenario
            trig = sq['trigger_quarter']
            dur = sq['duration']
            if trig <= t < trig + dur:
                stress_macro = sq['macro_override']
                stress_exit_extra = sq['extra_exit_rate']
                stress_zero_movin = sq['new_move_in_zero']
                stress_cost_inf = sq['cost_inflation']
                if t == trig and sq['trust_shock'] != 0:
                    brand_trust = max(0, brand_trust + sq['trust_shock'])

        # --- Macro economy ---
        if recession_remaining > 0:
            macro = params['recession_severity']
            recession_remaining -= 1
        else:
            macro = 1.0
            # Random recession check (quarterly prob)
            prob_map = {'stable': 0.03, 'moderate': 0.05, 'volatile': 0.08}
            ann_prob = prob_map.get(params.get('macro_volatility', 'stable'),
                                   params['recession_annual_prob'])
            if rng.random() < ann_prob / 4:
                recession_remaining = rng.randint(4, 9)  # 4-8 quarters
                macro = params['recession_severity']

        effective_macro = min(macro, stress_macro)

        # --- Cultural acceptance (annual growth) ---
        if t % 4 == 0 and t > 0:
            cultural_acceptance = min(1.0,
                cultural_acceptance + params['annual_acceptance_growth'])

        # --- Phase activation ---
        for i, phase in enumerate(phases):
            if phase.activated:
                # Check construction completion
                if not phase.construction_done:
                    if t >= phase.start_quarter + phase.construction_quarters:
                        phase.construction_done = True
                continue

            # Check activation conditions
            if i > 0 and phases[i - 1].activated:
                prev_occ = phases[i - 1].occupancy_rate
                daily_cost = (sum(ph.occupied for ph in phases if ph.activated)
                              * params['monthly_fee'] * 3 / 90)
                cash_days = (emergency_reserve / daily_cost
                             if daily_cost > 0 else 9999)
                construction_fund_ok = (capex_reserve >=
                    phase.total_units * cost_per_unit * 0.3)

                if (prev_occ >= params['phase_activation_threshold']
                        and cash_days >= params['min_cash_days_for_activation']
                        and construction_fund_ok):
                    phase.activated = True
                    phase.start_quarter = t
                    result.phase_activations[i] = t
                    # Deduct construction cost
                    build_cost = phase.total_units * cost_per_unit
                    capex_reserve -= build_cost * 0.3
                    operating_cash -= build_cost * 0.7
                    total_invested += build_cost

        # --- Compute totals ---
        total_occupied = sum(ph.occupied for ph in phases if ph.activated)
        total_units = sum(ph.total_units for ph in phases
                         if ph.activated and ph.construction_done)
        total_available = sum(ph.available_units for ph in phases)
        overall_occ = total_occupied / total_units if total_units > 0 else 0.0

        # --- New move-ins ---
        base_demand = params['target_pool'] * params['base_annual_conversion'] / 4

        trust_factor = brand_trust / 50.0
        trust_factor = max(0.1, min(3.0, trust_factor))

        # Insurance factor (active only after start quarter)
        ins_factor = 1.0
        if t >= params['insurance_start_quarter']:
            ins_factor = params['insurance_factor']

        # Cold start
        cold_start = min(1.0, max(0.2, (total_occupied / 800) ** 0.5))

        # Distance friction
        mkt_budget = params['marketing_budget_monthly']
        distance_friction = min(0.95, 0.85 + mkt_budget / 10_000_000 * 0.02)

        # Experience boost
        exp_boost = 1.0 + params['experience_level'] * 0.1

        # Onsen boost
        onsen_boost = 1.0 + onsen_boost_val

        # Market depletion
        market_depletion = min(1.0, market_pool / (initial_pool * 0.3))

        # Competitor impact
        competitor_diversion = 1.0
        if params.get('competitor_active', False):
            comp_q = params['competitor_year'] * 4
            if t == comp_q:
                comp_int = params.get('competitor_intensity', 'medium')
                shock = 5 if comp_int == 'medium' else 15
                brand_trust = max(0, brand_trust - shock)
            if t >= comp_q:
                comp_int = params.get('competitor_intensity', 'medium')
                div = 0.12 if comp_int == 'medium' else 0.30
                competitor_diversion = 1.0 - div

        # H Hotel contribution
        h_hotel_contrib = 0
        if params['h_hotel_active']:
            contacts = params['h_hotel_annual_contacts']
            inq = params['h_hotel_inquiry_rate']
            close = params['h_hotel_close_rate']
            h_hotel_contrib = contacts * inq * close / 4

        new_movin = (base_demand * trust_factor * ins_factor * cold_start
                     * effective_macro * distance_friction * exp_boost
                     * medical_boost * onsen_boost * market_depletion
                     * competitor_diversion
                     + h_hotel_contrib)

        if stress_zero_movin:
            new_movin = 0

        # Cap at 15% of available units
        max_movin = int(total_available * 0.15) if total_available > 0 else 0
        new_movin = max(0, min(int(new_movin), max_movin))

        # Distribute new move-ins across phases (fill earlier phases first)
        remaining_movin = new_movin
        for phase in phases:
            if not phase.activated or not phase.construction_done:
                continue
            can_take = phase.available_units
            take = min(remaining_movin, can_take)
            if take > 0:
                phase.occupied += take
                # New residents age 65-75
                new_ages = rng.uniform(65, 75, size=take).tolist()
                phase.resident_ages.extend(new_ages)
                remaining_movin -= take
            if remaining_movin <= 0:
                break

        actual_movin = new_movin - remaining_movin

        # Consume market pool
        market_pool = max(0, market_pool - actual_movin)

        # Market replenishment (annual) — 規格書原始機制，預設 4%/年
        if t % 4 == 0 and t > 0:
            replenish = market_pool * params['market_replenishment_rate']
            market_pool += replenish

        # --- Exits (deaths + voluntary + care transfer) ---
        total_exits = 0
        total_refund_amount = 0.0
        for phase in phases:
            if not phase.activated or phase.occupied == 0:
                continue

            # Age all residents by 0.25 years
            phase.resident_ages = [a + 0.25 for a in phase.resident_ages]

            # Calculate exit rates based on age distribution
            if len(phase.resident_ages) == 0:
                continue

            avg_age = np.mean(phase.resident_ages)
            mortality_rate = _lookup_rate(avg_age, AGE_MORTALITY_TABLE)
            care_rate = _lookup_rate(avg_age, AGE_CARE_TRANSFER_TABLE)
            quarterly_exit_rate = (mortality_rate + ANNUAL_VOLUNTARY_EXIT_RATE
                                   + care_rate) / 4 + stress_exit_extra / 4

            n_exit = int(phase.occupied * quarterly_exit_rate)
            n_exit = min(n_exit, phase.occupied)

            if n_exit > 0:
                # Remove oldest residents first
                phase.resident_ages.sort(reverse=True)
                removed_ages = phase.resident_ages[:n_exit]
                phase.resident_ages = phase.resident_ages[n_exit:]
                phase.occupied -= n_exit
                total_exits += n_exit

                # Refund calculation
                for age in removed_ages:
                    # P9: 用入住年齡中位數 70（65-75 均勻分佈），而非固定值
                    avg_move_in_age = 70  # mean of uniform(65, 75)
                    years_in = max(0, age - avg_move_in_age)
                    years_in = max(0, min(25, years_in))
                    amort_years = params['refund_amortization_years']
                    if amort_years > 0:
                        effective_rate = max(0,
                            params['refund_percentage']
                            * (1 - years_in / amort_years))
                    else:
                        effective_rate = params['refund_percentage']
                    total_refund_amount += params['deposit_amount'] * effective_rate

        # --- Brand trust update ---
        # Collect age data first
        all_ages = []
        for ph in phases:
            if ph.activated:
                all_ages.extend(ph.resident_ages)
        if all_ages:
            med_age = float(np.median(all_ages))
            p80 = sum(1 for a in all_ages if a > 80) / len(all_ages)
        else:
            med_age = 70.0
            p80 = 0.0

        # Inflows（規格書原始公式）
        if overall_occ > 0.85:
            brand_trust += 2.0  # word of mouth
        elif overall_occ > 0.70:
            brand_trust += 0.5
        trust_mech_bonus = params['trust_mechanism_level'] * 1.5
        brand_trust += trust_mech_bonus

        # Cultural acceptance helps brand
        brand_trust += cultural_acceptance * 0.5

        # Occupancy itself builds some trust
        if total_occupied > 100:
            brand_trust += 0.3

        base_decay = params.get('brand_base_decay', 0.5)
        aging_decay = 0.0
        if med_age > 75:
            aging_decay = (med_age - 75) * 0.1
        modified_decay = (base_decay + aging_decay) * (1 - total_decay_reduction)
        brand_trust -= modified_decay

        # Random negative event (2% per quarter)
        if rng.random() < 0.02:
            shock = rng.uniform(10, 30)
            brand_trust -= shock
            # Recovery: track the deficit and recover 4% per quarter
            # (simplified: just clamp and allow natural recovery)

        # Squeeze pressure on trust (only significant backlog)
        total_funds_check = operating_cash + emergency_reserve + deposit_pool
        if refund_backlog > total_funds_check * 0.1 and refund_backlog > 0:
            brand_trust *= 0.95  # gentler penalty

        brand_trust = max(0, min(100, brand_trust))

        # Brand vitality
        vitality = max(0, 100 - max(0, (med_age - 70)) * 5 - p80 * 100)

        # --- Operational capability ---
        # 規格書原始線性公式 + 下限
        suao_penalty = 2.0  # labor market penalty
        cap_change = (1.0 * params.get('team_quality', 0.8)
                      - params.get('staff_turnover', 0.15) * 2
                      - suao_penalty * 0.5)
        ops_floor = params.get('ops_capability_floor', 10)
        operational_capability = max(ops_floor, min(100,
            operational_capability + cap_change))

        # --- Revenue ---
        # P7: 月費隨通膨調漲（漲幅 = 成本通膨的 70%，高齡住戶對漲價敏感）
        fee_inflation = cost_inflation_accum ** params.get('fee_inflation_ratio', 0.0)
        adjusted_monthly_fee = params['monthly_fee'] * fee_inflation
        fee_revenue = total_occupied * adjusted_monthly_fee * 3  # quarterly

        # New deposits
        deposit_revenue = actual_movin * params['deposit_amount']

        # Revenue streams
        stream_revenue = 0.0
        active_streams = params.get('revenue_streams', [])
        for stream_name in active_streams:
            if stream_name not in REVENUE_STREAM_OPTIONS:
                continue
            sinfo = REVENUE_STREAM_OPTIONS[stream_name]

            # Check prerequisites
            if sinfo['requires_onsen'] and params.get('onsen_level', 0) == 0:
                continue
            if sinfo['requires_ccrc'] and params['ccrc_care_ratio'] < 0.05:
                continue
            if sinfo['requires_trust'] > 0 and brand_trust < sinfo['requires_trust']:
                continue

            # Track when stream started
            if stream_name not in revenue_stream_start:
                revenue_stream_start[stream_name] = t

            quarters_active = t - revenue_stream_start[stream_name]
            ramp = min(1.0, quarters_active / max(1, sinfo['ramp_quarters']))

            q_rev = sinfo['monthly_revenue'] * 3 * ramp
            if sinfo['scales_with_occupancy']:
                q_rev *= overall_occ

            stream_revenue += q_rev

        # Medical external revenue
        medical_ext_rev = 0
        if params.get('medical_external_revenue', False):
            medical_ext_rev = params['medical_integration'] * 5_000_000 * 3

        # Onsen external revenue
        onsen_ext_rev = 0
        onsen_preset_data = None
        if params.get('onsen_level', 0) > 0:
            from .parameters import ONSEN_PRESETS
            for name, data in ONSEN_PRESETS.items():
                if data['onsen_level'] == params['onsen_level']:
                    onsen_ext_rev = data.get('onsen_external_revenue', 0) * 3
                    break

        total_revenue = (fee_revenue + deposit_revenue + stream_revenue
                         + medical_ext_rev + onsen_ext_rev)

        # --- Costs ---
        # Staff costs
        staff_count = total_occupied * params['staff_ratio']
        staff_cost = (staff_count * params['avg_staff_cost_monthly']
                      * params['suao_labor_premium'] * 3)

        # Onsen maintenance
        onsen_maint = staff_cost * (params['onsen_cost_multiplier'] - 1.0)

        # Medical costs
        med_cost = 0
        if params['medical_integration'] == 1:
            med_cost = 3_000_000 * 3
        elif params['medical_integration'] == 2:
            med_cost = 8_000_000 * 3
        elif params['medical_integration'] == 3:
            med_cost = 25_000_000 * 3

        # Experience marketing
        exp_cost = params.get('experience_cost_monthly', 2_000_000) * 3

        # Marketing
        mkt_cost = params['marketing_budget_monthly'] * 3

        # Capital cost (only on invested capital, not full budget)
        capital_cost = total_invested * params['annual_cost_of_capital'] / 4

        # Regulation compliance
        reg_cost = params.get('regulation_compliance_cost', 0) / 4

        # Revenue share
        rev_share = total_revenue * params.get('op_partner_revenue_share', 0)

        # Cost inflation from stress
        if stress_cost_inf > 0:
            cost_inflation_accum *= (1 + stress_cost_inf / 4)

        # Brand aging countermeasure costs
        cm_cost = sum(
            BRAND_AGING_OPTIONS.get(c, {}).get('cost_per_cycle', 0)
            for c in countermeasures
        ) / 100  # amortized quarterly

        total_cost = ((staff_cost + onsen_maint + med_cost + exp_cost
                       + mkt_cost + capital_cost + reg_cost + rev_share
                       + cm_cost) * cost_inflation_accum)

        # --- Refund payments ---
        refund_backlog += total_refund_amount
        if params.get('trust_independent', False):
            # Pay from trust pool, max 10% per quarter
            max_refund = deposit_pool * 0.10
            actual_refund = min(refund_backlog, max_refund)
            deposit_pool -= actual_refund
        else:
            # P4: 下限為 0，避免 operating_cash 為負時退費為負數
            actual_refund = min(refund_backlog, max(0, operating_cash + deposit_revenue))

        refund_backlog = max(0, refund_backlog - actual_refund)

        # --- Update financial pools ---
        net_cf = total_revenue - total_cost - actual_refund

        if params.get('trust_independent', False):
            deposit_pool += deposit_revenue
        else:
            operating_cash += deposit_revenue

        operating_cash += fee_revenue + stream_revenue + medical_ext_rev + onsen_ext_rev
        operating_cash -= total_cost
        if not params.get('trust_independent', False):
            operating_cash -= actual_refund

        # Transfer 20% of operating surplus to emergency
        if operating_cash > 0:
            transfer = operating_cash * 0.05  # 5% per quarter ≈ 20% annual
            emergency_reserve += transfer
            operating_cash -= transfer

        # Refinance risk (every 5 years)
        if params.get('refinance_risk', False) and t > 0 and t % 20 == 0:
            if rng.random() < 0.10:
                params = dict(params)
                params['annual_cost_of_capital'] *= 1.5

        cumulative_cf += net_cf

        # --- Record cashflow breakdown ---
        result.cf_deposit_income[t] = deposit_revenue
        result.cf_monthly_fee[t] = fee_revenue
        result.cf_other_revenue[t] = stream_revenue + medical_ext_rev + onsen_ext_rev
        result.cf_construction[t] = sum(
            ph.total_units * cost_per_unit
            for ph in phases if ph.start_quarter == t
        )
        result.cf_operating[t] = total_cost - capital_cost  # operating without capital cost
        result.cf_refund[t] = actual_refund
        result.cf_capital_cost[t] = capital_cost

        # --- Record results ---
        result.total_occupied[t] = sum(ph.occupied for ph in phases)
        result.total_units_active[t] = total_units
        result.occupancy_rate[t] = overall_occ

        result.deposit_trust_pool[t] = deposit_pool
        result.operating_cashflow[t] = operating_cash
        result.capex_reserve[t] = capex_reserve
        result.emergency_reserve[t] = emergency_reserve
        result.cumulative_cashflow[t] = cumulative_cf
        result.quarterly_revenue[t] = total_revenue
        result.quarterly_cost[t] = total_cost + actual_refund
        result.quarterly_net[t] = net_cf

        result.brand_trust[t] = brand_trust
        result.brand_vitality[t] = vitality
        result.operational_capability[t] = operational_capability
        result.median_age[t] = med_age
        result.pct_over_80[t] = p80

        result.market_pool_remaining[t] = market_pool
        result.cultural_acceptance[t] = cultural_acceptance
        result.macro_factor[t] = effective_macro

        result.new_move_ins[t] = actual_movin
        result.exits[t] = total_exits
        result.refund_due[t] = total_refund_amount
        result.refund_paid[t] = actual_refund
        result.refund_backlog[t] = refund_backlog

        for i, ph in enumerate(phases):
            if ph.activated:
                result.phase_occupancy[i][t] = ph.occupancy_rate

        # --- Evaluate 10 rules ---
        rules = np.zeros(10, dtype=int)
        squeeze_pressure = refund_backlog / max(1, deposit_pool + operating_cash)

        # R01: Deposit squeeze spiral
        if overall_occ < 0.80 and not params.get('trust_independent') and squeeze_pressure > 0.8:
            rules[0] = 2
        elif overall_occ < 0.85 and squeeze_pressure > 0.5:
            rules[0] = 1

        # R02: Growth flywheel (positive)
        if overall_occ > 0.85 and brand_trust > 60 and ins_factor > 1.5:
            rules[1] = 2  # 2 = active positive

        # R03: Brand aging bomb
        if med_age > 75 and vitality < 50:
            rules[2] = 2
        elif med_age > 73 and vitality < 60:
            rules[2] = 1

        # R04: Trust capital flywheel (positive)
        if params['trust_mechanism_level'] >= 2 and brand_trust > 50 and squeeze_pressure < 0.3:
            rules[3] = 2

        # R05: Ghost town trap
        total_sold = sum(ph.occupied for ph in phases)
        total_cap = sum(ph.total_units for ph in phases if ph.activated)
        sales_pct = total_sold / total_cap if total_cap > 0 else 0
        if sales_pct > 0.80 and overall_occ < 0.50:
            rules[4] = 2
        elif sales_pct > 0.60 and overall_occ < 0.60:
            rules[4] = 1

        # R06: Scale x deficiency amplification
        active_units = sum(ph.total_units for ph in phases if ph.activated)
        if active_units > 1000 and (
            not params.get('trust_independent')
            or ins_factor < 1.5
            or overall_occ < 0.75
        ):
            rules[5] = 2
        elif active_units > 500:
            rules[5] = 1

        # R07: Medical x brand tension
        if params['medical_integration'] < 2 and params['debranding_level'] > 2:
            rules[6] = 2
        elif params['medical_integration'] < 2 and params['debranding_level'] > 1:
            rules[6] = 1

        # R08: Suao distance friction
        if params['experience_level'] < 1 and params.get('onsen_level', 0) < 2:
            rules[7] = 2 if distance_friction < 0.87 else 1

        # R09: Operational capability gap
        if operational_capability < 40 and overall_occ > 0.50:
            rules[8] = 2
        elif operational_capability < 50 and overall_occ > 0.40:
            rules[8] = 1

        # R10: Insurance flywheel missing
        if ins_factor < 1.5 and active_units > 500:
            rules[9] = 2
        elif ins_factor < 1.5 and active_units > 200:
            rules[9] = 1

        result.rules_status[t] = rules

        # --- Check for collapse（依信託等級分兩套邏輯）---
        if params.get('trust_mechanism_level', 0) >= 2:
            # 信託模式：押金隔離，不算可動用資金
            available_funds = operating_cash + emergency_reserve
        else:
            # 非信託模式：押金混入營運（規格書設計，捕捉擠兌風險）
            available_funds = operating_cash + emergency_reserve + deposit_pool

        net_liquidity = available_funds - refund_backlog

        if result.failed_quarter < 0:
            if available_funds < 0:
                result.failed_quarter = t
            elif net_liquidity < 0:
                consecutive_illiquid += 1
                if consecutive_illiquid >= params.get('liquidity_crisis_quarters', 4):
                    result.failed_quarter = t
            else:
                consecutive_illiquid = 0

    return result
