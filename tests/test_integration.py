"""Tests d'intégration de PostgresStore (TD 5).

Nécessitent une base PostgreSQL : ignorés si DATABASE_URL n'est pas définie.
"""

import os
import uuid

import pytest

from fleet_api.models import Position, Reading
from fleet_api.store import PostgresStore

DSN = os.environ.get("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DSN, reason="DATABASE_URL non définie"),
]


@pytest.fixture(scope="module")
def store() -> PostgresStore:
    assert DSN is not None
    return PostgresStore(DSN)


@pytest.fixture
def robot_id() -> str:
    """Identifiant unique : isole chaque test sans vider la table."""
    return f"robot-{uuid.uuid4().hex[:8]}"


def make_reading(robot_id: str, ts: float, charging: bool = False) -> Reading:
    return Reading(
        robot_id=robot_id,
        timestamp_s=ts,
        voltage_mv=12_000,
        position=Position(x=1.5, y=-2.5),
        is_charging=charging,
    )


def test_ping(store):
    assert store.ping() is True


def test_latest_robot_inconnu(store, robot_id):
    assert store.latest(robot_id) is None


def test_add_puis_latest_aller_retour(store, robot_id):
    reading = make_reading(robot_id, 1000.0, charging=True)
    store.add(reading)
    assert store.latest(robot_id) == reading


def test_latest_renvoie_la_plus_recente(store, robot_id):
    store.add(make_reading(robot_id, 1000.0))
    store.add(make_reading(robot_id, 3000.0))
    store.add(make_reading(robot_id, 2000.0))
    latest = store.latest(robot_id)
    assert latest is not None
    assert latest.timestamp_s == 3000.0


def test_history_ordre_decroissant(store, robot_id):
    for ts in (1.0, 3.0, 2.0):
        store.add(make_reading(robot_id, ts))
    assert [r.timestamp_s for r in store.history(robot_id)] == [3.0, 2.0, 1.0]


def test_history_respecte_la_limite(store, robot_id):
    for ts in range(5):
        store.add(make_reading(robot_id, float(ts)))
    assert len(store.history(robot_id, limit=2)) == 2


def test_history_isole_les_robots(store, robot_id):
    autre = f"{robot_id}-autre"
    store.add(make_reading(robot_id, 1.0))
    store.add(make_reading(autre, 2.0))
    assert {r.robot_id for r in store.history(robot_id)} == {robot_id}


def test_latest_all_une_mesure_par_robot(store, robot_id):
    autre = f"{robot_id}-autre"
    store.add(make_reading(robot_id, 1.0))
    store.add(make_reading(robot_id, 2.0))
    store.add(make_reading(autre, 5.0))
    par_robot = {r.robot_id: r for r in store.latest_all()}
    assert par_robot[robot_id].timestamp_s == 2.0
    assert par_robot[autre].timestamp_s == 5.0
