-- Demo seed data -- run after schema.sql / migrations, for local dev and demo only.

INSERT INTO users (id, full_name, phone_number, email, region) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Test User One', '+919990000001', 'user1@example.com', 'Jaipur'),
    ('22222222-2222-2222-2222-222222222222', 'Test User Two', '+919990000002', 'user2@example.com', 'Jodhpur')
ON CONFLICT (id) DO NOTHING;

INSERT INTO devices (id, user_id, device_type, device_name) VALUES
    ('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', 'phone', 'Demo Phone A'),
    ('44444444-4444-4444-4444-444444444444', '22222222-2222-2222-2222-222222222222', 'wearable', 'Demo Band B')
ON CONFLICT (id) DO NOTHING;

INSERT INTO biometric_readings (user_id, device_id, heart_rate, spo2, skin_temp, steps, recorded_at) VALUES
    ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 78, 98, 36.6, 1200, now() - interval '1 hour'),
    ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 145, 91, 37.2, 40, now() - interval '10 minutes'),
    ('22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444444', 82, 96, 36.9, 3400, now() - interval '30 minutes');

INSERT INTO environmental_readings (region, temperature, heat_index, aqi, rainfall_mm, flood_risk_level, source, recorded_at) VALUES
    ('Jaipur', 39.2, 42.5, 140, 0, 'low', 'IMD', now() - interval '1 hour'),
    ('Jodhpur', 41.0, 44.0, 210, 0, 'low', 'CPCB', now() - interval '1 hour');

-- One risk score per biometric reading above, matching the risk engine's expected output shape.
INSERT INTO risk_scores (user_id, score, risk_level, contributing_factors, computed_at) VALUES
    ('11111111-1111-1111-1111-111111111111', 5, 'low',
        '{"heart_rate": {"value": 78, "issue": null}}'::jsonb, now() - interval '1 hour'),
    ('11111111-1111-1111-1111-111111111111', 65, 'critical',
        '{"heart_rate": {"value": 145, "issue": "tachycardia_threshold"}, "spo2": {"value": 91, "issue": "low_spo2_threshold"}}'::jsonb,
        now() - interval '10 minutes'),
    ('22222222-2222-2222-2222-222222222222', 5, 'low',
        '{"heart_rate": {"value": 82, "issue": null}}'::jsonb, now() - interval '30 minutes');

-- Alert generated off the critical risk score for user one.
INSERT INTO alerts (user_id, risk_score_id, alert_type, channel, message, delivery_status, sent_at)
SELECT '11111111-1111-1111-1111-111111111111', rs.id, 'critical', 'both',
       'Heart rate 145 bpm and SpO2 91% both breached safe thresholds.', 'pending', rs.computed_at
FROM risk_scores rs
WHERE rs.user_id = '11111111-1111-1111-1111-111111111111' AND rs.risk_level = 'critical'
LIMIT 1;

INSERT INTO consent_logs (user_id, data_category, purpose) VALUES
    ('11111111-1111-1111-1111-111111111111', 'biometric', 'hazard_alerting'),
    ('22222222-2222-2222-2222-222222222222', 'biometric', 'hazard_alerting');

-- Demo EEG session + prediction for Phase 2 (not part of MVP judging flow).
INSERT INTO eeg_sessions (id, user_id, device_id, started_at, ended_at, sample_rate_hz) VALUES
    ('55555555-5555-5555-5555-555555555555', '11111111-1111-1111-1111-111111111111', NULL,
     now() - interval '2 hours', now() - interval '1 hour 50 minutes', 256)
ON CONFLICT (id) DO NOTHING;

INSERT INTO eeg_predictions (session_id, predicted_class, confidence, window_start_ms) VALUES
    ('55555555-5555-5555-5555-555555555555', 'healthy', 0.97, 0);
