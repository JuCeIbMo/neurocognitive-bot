"""Tests for deterministic lead transition logic."""

import pytest

from app.graph.lead.transitions import (
    determine_next_phase,
    _check_eligibility,
)


class TestEligibility:
    def test_fisioterapeuta_is_eligible(self):
        assert _check_eligibility("fisioterapeuta", None) is True

    def test_kinesiologo_is_eligible(self):
        assert _check_eligibility("kinesiólogo", None) is True

    def test_terapeuta_ocupacional_is_eligible(self):
        assert _check_eligibility("terapeuta ocupacional", None) is True

    def test_entrenador_personal_not_eligible(self):
        assert _check_eligibility("entrenador personal", None) is False

    def test_nutriologo_not_eligible(self):
        assert _check_eligibility("nutriólogo", None) is False

    def test_last_year_student_is_eligible(self):
        assert _check_eligibility("estudiante", True) is True

    def test_unknown_profession_not_eligible(self):
        assert _check_eligibility("algo raro", None) is False

    def test_partial_match_fisioterapia(self):
        assert _check_eligibility("licenciado en fisioterapia", None) is True


class TestPhaseTransitions:
    def test_discovery_stays_without_info(self):
        state = {"phase": "discovery"}
        assert determine_next_phase(state) == "discovery"

    def test_discovery_to_pain_when_eligible(self):
        state = {
            "phase": "discovery",
            "profession": "fisioterapeuta",
            "experience": "practicing",
            "is_eligible": True,
        }
        assert determine_next_phase(state) == "pain"

    def test_discovery_to_redirect_when_not_eligible(self):
        state = {
            "phase": "discovery",
            "profession": "entrenador personal",
            "is_eligible": False,
        }
        assert determine_next_phase(state) == "redirect"

    def test_discovery_stays_with_only_profession(self):
        state = {
            "phase": "discovery",
            "profession": "fisioterapeuta",
            "is_eligible": True,
        }
        assert determine_next_phase(state) == "discovery"

    def test_pain_stays_without_frustration(self):
        state = {"phase": "pain", "frustration_articulated": False}
        assert determine_next_phase(state) == "pain"

    def test_pain_to_gap(self):
        state = {"phase": "pain", "frustration_articulated": True}
        assert determine_next_phase(state) == "gap"

    def test_gap_to_solution(self):
        state = {"phase": "gap", "gap_acknowledged": True}
        assert determine_next_phase(state) == "solution"

    def test_solution_to_closing(self):
        state = {"phase": "solution", "interest_expressed": True}
        assert determine_next_phase(state) == "closing"

    def test_closing_to_done(self):
        state = {"phase": "closing", "payment_link_sent": True}
        assert determine_next_phase(state) == "done"

    def test_closing_stays_without_payment(self):
        state = {"phase": "closing", "payment_link_sent": False}
        assert determine_next_phase(state) == "closing"
