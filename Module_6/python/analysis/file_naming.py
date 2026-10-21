"""Stable asset names shared by analysis and report generation."""


def gain_token(value):
    return f"{value:g}".replace(".", "p")


def experiment_stem(kp, ki=None):
    if ki is None:
        return f"exp_p_kp_{gain_token(kp)}"
    return f"exp_pi_kp_{gain_token(kp)}_ki_{gain_token(ki)}"


def simulation_stem(label):
    return {
        "P025": "sim_two_lump_p_kp_0p25",
        "P4": "sim_two_lump_p_kp_4",
        "P100": "sim_two_lump_p_kp_100",
        "PI01": "sim_two_lump_pi_kp_20_ki_0p1",
        "PI02": "sim_two_lump_pi_kp_20_ki_0p2",
        "PI05": "sim_two_lump_pi_kp_20_ki_0p5",
    }[label]
