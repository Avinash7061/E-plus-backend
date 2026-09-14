"""Pure unit tests for alert_dispatcher.py — Twilio is mocked, no real sends."""

from unittest.mock import patch, MagicMock
from app.services import alert_dispatcher


def test_should_alert_false_for_low_moderate():
    assert alert_dispatcher.should_alert("low") is False
    assert alert_dispatcher.should_alert("moderate") is False


def test_should_alert_true_for_high_critical():
    assert alert_dispatcher.should_alert("high") is True
    assert alert_dispatcher.should_alert("critical") is True


def test_message_under_160_chars():
    message = alert_dispatcher.build_alert_message(
        "critical",
        {"heart_rate": 150, "heat_index": 46, "spo2": 88, "aqi": 250},
    )
    assert len(message) <= 160


def test_message_has_no_diagnostic_language():
    message = alert_dispatcher.build_alert_message("high", {"heart_rate": 130})
    lowered = message.lower()
    assert "diagnos" not in lowered


@patch("app.services.alert_dispatcher.TwilioClient")
def test_send_sms_alert_returns_false_on_exception(mock_twilio_client):
    from twilio.base.exceptions import TwilioRestException

    mock_instance = MagicMock()
    mock_instance.messages.create.side_effect = TwilioRestException(
        status=400, uri="fake", msg="bad request"
    )
    mock_twilio_client.return_value = mock_instance

    with patch("app.services.alert_dispatcher.settings") as mock_settings:
        mock_settings.twilio_account_sid = "fake_sid"
        mock_settings.twilio_auth_token = "fake_token"
        mock_settings.twilio_from_number = "+10000000000"

        result = alert_dispatcher.send_sms_alert("+19999999999", "test message")

    assert result is False


def test_dispatch_alert_returns_none_when_not_warranted():
    mock_db = MagicMock()
    result = alert_dispatcher.dispatch_alert(
        user_id="user-1",
        phone_number="+19999999999",
        risk_score_id=1,
        risk_level="low",
        contributing_factors={},
        db=mock_db,
    )
    assert result is None
    mock_db.table.assert_not_called()