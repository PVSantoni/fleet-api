"""Tests du module de télémétrie.

Deux tests vous sont fournis en exemple : ils montrent le style attendu.
Tout le reste est à écrire — voir le TD 1.
"""

import pytest

from fleet_api.models import Position, Reading, RobotState
from fleet_api.telemetry import (
    average_speed_mps,
    battery_percentage,
    detect_voltage_dropouts,
    distance_m,
    estimate_runtime_minutes,
    fleet_summary,
    is_low_battery,
    median_voltage_mv,
    path_length_m,
    robot_state,
)

# ---------------------------------------------------------------------------
# Exemple 1 — un test simple, avec un cas nominal et les deux bornes.
# ---------------------------------------------------------------------------


def test_battery_percentage_bornes_et_cas_nominal():
    """La conversion est linéaire et bornée à [0, 100]."""
    assert battery_percentage(12_600) == 100.0
    assert battery_percentage(10_500) == 0.0
    assert battery_percentage(11_550) == 50.0
    # Hors bornes : on sature, on ne dépasse pas.
    assert battery_percentage(13_000) == 100.0
    assert battery_percentage(9_000) == 0.0


# ---------------------------------------------------------------------------
# Exemple 2 — le même test écrit en paramétré, quand les cas se ressemblent.
# On teste aussi que l'erreur attendue est bien levée.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        (Position(0, 0), Position(3, 4), 5.0),  # triplet pythagoricien
        (Position(0, 0), Position(0, 0), 0.0),  # distance à soi-même
        (Position(1, 1), Position(-2, -3), 5.0),  # coordonnées négatives
        (Position(3, 4), Position(0, 0), 5.0),  # symétrie
    ],
)
def test_distance_m(a, b, attendu):
    """La distance est euclidienne, positive et symétrique."""
    assert distance_m(a, b) == pytest.approx(attendu)


def test_battery_percentage_rejette_des_bornes_incoherentes():
    """Une plage de tension invalide lève une ValueError."""
    with pytest.raises(ValueError, match="strictement supérieur"):
        battery_percentage(11_000, empty_mv=12_000, full_mv=11_000)


# ---------------------------------------------------------------------------
# À vous. Huit fonctions de fleet_api.telemetry n'ont aucun test :
#
#   is_low_battery, path_length_m, average_speed_mps, estimate_runtime_minutes,
#   median_voltage_mv, robot_state, detect_voltage_dropouts, fleet_summary
#
# Écrivez-les en vous appuyant sur les docstrings, qui font foi.
# Trois de ces fonctions ne respectent pas leur spécification.
# ---------------------------------------------------------------------------


def test_low_battery_pct():
    """Test de la fonction is_low_battery."""
    

    assert is_low_battery(18) is True
    assert is_low_battery(20) is True
    assert is_low_battery(22) is False
    

def test_path_length_m():
    """Test de la fonction path_length_m."""
    positions = [Position(0, 0), Position(3, 4), Position(6, 8)]
    assert path_length_m(positions) == pytest.approx(10.0)
    assert path_length_m([Position(0, 0)]) == 0.0
    assert path_length_m([]) == 0.0


def test_average_speed_mps():
    """La vitesse moyenne est indisponible pour une durée non positive."""
    assert average_speed_mps(10.0, 5.0) == pytest.approx(2.0)
    assert average_speed_mps(10.0, 0.0) is None
    assert average_speed_mps(10.0, -1.0) is None
        
        

def test_estimate_runtime_minutes():
    """Test de la fonction estimate_runtime_minutes."""
    assert estimate_runtime_minutes(50, 5) == 10.0
    assert estimate_runtime_minutes(100, 10) == 10.0
    assert estimate_runtime_minutes(0, 5) == 0.0
    assert estimate_runtime_minutes(50, 0) is None
    assert estimate_runtime_minutes(50, -5) is None


def test_median_voltage_mv():
    """La médiane fonctionne pour un nombre impair ou pair de mesures."""
    assert median_voltage_mv([]) is None

    readings = [
        Reading("r1", 1.0, 12_000, Position(0, 0)),
        Reading("r1", 2.0, 11_000, Position(0, 0)),
        Reading("r1", 3.0, 11_500, Position(0, 0)),
    ]
    assert median_voltage_mv(readings) == 11_500

    readings_pair = [
        Reading("r1", 1.0, 13_000, Position(0, 0)),
        Reading("r1", 2.0, 10_000, Position(0, 0)),
        Reading("r1", 3.0, 12_000, Position(0, 0)),
        Reading("r1", 4.0, 11_000, Position(0, 0)),
    ]
    assert median_voltage_mv(readings_pair) == 11_500


def test_robot_state():
    """Les états suivent l'ordre de priorité indiqué dans la docstring."""
    offline = Reading("r1", 0.0, 10_500, Position(0, 0))
    charging = Reading("r1", 100.0, 10_500, Position(0, 0), is_charging=True)
    low_battery = Reading("r1", 100.0, 10_500, Position(0, 0))
    operational = Reading("r1", 100.0, 12_600, Position(0, 0))

    assert robot_state(offline, now_s=121.0) is RobotState.OFFLINE
    assert robot_state(charging, now_s=100.0) is RobotState.CHARGING
    assert robot_state(low_battery, now_s=100.0) is RobotState.LOW_BATTERY
    assert robot_state(operational, now_s=100.0) is RobotState.OPERATIONAL
    
def test_fleet_summary_empty():
    """Une flotte vide retourne un résumé vide valide."""
    assert fleet_summary([]) == {
        "robot_count": 0,
        "average_battery_pct": 0.0,
        "low_battery_count": 0,
    }


def test_detect_voltage_dropouts():
    """Seules les baisses strictement supérieures à la limite sont signalées."""
    readings = [
        Reading("r1", 1.0, 12_000, Position(0, 0)),
        Reading("r1", 2.0, 11_900, Position(0, 0)),
        Reading("r1", 3.0, 11_700, Position(0, 0)),
        Reading("r1", 4.0, 11_800, Position(0, 0)),
    ]

    assert detect_voltage_dropouts(readings, max_drop_mv=150) == [2]
    assert detect_voltage_dropouts([], max_drop_mv=150) == []