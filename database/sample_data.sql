-- ================================
-- Sample / Dummy Data
-- AI Voice Hospital System
-- ================================

-- ----------------
-- Doctors
-- ----------------
INSERT INTO doctors (
    name,
    department,
    qualification,
    experience_years,
    available_days
) VALUES
('Dr. Mehta', 'Cardiology', 'MD Cardiology', 12, 'Mon-Fri'),
('Dr. Sharma', 'General', 'MBBS', 8, 'Mon-Sat'),
('Dr. Rao', 'ENT', 'MS ENT', 10, 'Tue-Sun');

-- ----------------
-- Patients
-- ----------------
INSERT INTO patients (
    name,
    age,
    gender,
    phone,
    preferred_language,
    created_at
) VALUES
('Amit Patil', 45, 'Male', '9999999999', 'mr', '2026-01-07'),
('Sneha Kulkarni', 30, 'Female', '8888888888', 'en', '2026-01-07'),
('Rahul Verma', 52, 'Male', '7777777777', 'hi', '2026-01-07');

-- ----------------
-- Appointments
-- ----------------
INSERT INTO appointments (
    patient_id,
    doctor_id,
    appointment_date,
    appointment_time,
    status,
    reason,
    booking_source,
    language_used,
    created_at
) VALUES
(1, 2, '2026-01-10', '10:30', 'Booked', 'General consultation', 'voice', 'mr', '2026-01-07'),
(2, 1, '2026-01-11', '11:00', 'Booked', 'Chest pain', 'voice', 'en', '2026-01-07'),
(3, 3, '2026-01-12', '12:15', 'Booked', 'Ear discomfort', 'voice', 'hi', '2026-01-07');
