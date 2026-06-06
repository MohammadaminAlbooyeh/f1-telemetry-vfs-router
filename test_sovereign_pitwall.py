"""
Unit Tests for Sovereign Pit-Wall Safety System
IBM AI Builders Challenge - Formula 1 Telemetry Edge Computing
"""

import unittest
import struct
import sys
from sovereign_pitwall_poc import (
    phase1_vfs_ingestion,
    phase5_surgical_strike,
    ibm_granite_decision_engine,
    generate_granite_analysis,
    WEIGHTS,
    CRITICAL_HDI_THRESHOLD,
    REDLINE_VETO
)


class TestVFSLayer(unittest.TestCase):
    """Test Layer 1: Sovereign VFS Binary Packing"""

    def test_binary_packing_normal_data(self):
        """Test binary packing of normal telemetry data"""
        binary_chunk = phase1_vfs_ingestion(10)
        self.assertEqual(len(binary_chunk), 24)  # 6 unsigned ints * 4 bytes

    def test_binary_packing_stress_scenario(self):
        """Test binary packing with stress values"""
        binary_chunk = phase1_vfs_ingestion(28)  # Second 28: fatigue spike
        self.assertEqual(len(binary_chunk), 24)

    def test_binary_unpacking(self):
        """Test unpacking binary data without corruption"""
        binary_chunk = phase1_vfs_ingestion(5)
        unpacked = phase5_surgical_strike(binary_chunk)

        # Verify all 6 parameters unpacked
        self.assertEqual(len(unpacked), 6)
        self.assertIn('tyres', unpacked)
        self.assertIn('driver_fatigue', unpacked)
        self.assertIn('thermal', unpacked)
        self.assertIn('hydraulics', unpacked)
        self.assertIn('brakes', unpacked)
        self.assertIn('fuel_system', unpacked)

    def test_struct_module_integrity(self):
        """Test that struct packing/unpacking is lossless"""
        test_values = (35, 60, 45, 25, 30, 15)
        packed = struct.pack('6I', *test_values)
        unpacked = struct.unpack('6I', packed)
        self.assertEqual(test_values, unpacked)


class TestAIDecisionEngine(unittest.TestCase):
    """Test Layer 2: IBM Granite AI Decision Engine"""

    def test_redline_veto_trigger(self):
        """Test Redline Veto triggers when single parameter exceeds 85"""
        telemetry = {
            'tyres': 45,
            'driver_fatigue': 88,  # Exceeds REDLINE_VETO
            'thermal': 50,
            'hydraulics': 20,
            'brakes': 30,
            'fuel_system': 15,
            'timestamp': 28
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        self.assertTrue(pit_triggered)
        self.assertIn('FATIGUE', status)

    def test_cascading_failure_trigger(self):
        """Test Cascading Failure Trigger when HDI exceeds 70"""
        telemetry = {
            'tyres': 75,
            'driver_fatigue': 75,
            'thermal': 75,
            'hydraulics': 75,
            'brakes': 75,
            'fuel_system': 75,
            'timestamp': 15
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        # HDI will be 75 * 1.0 (sum of weights) = 75
        self.assertTrue(hdi >= CRITICAL_HDI_THRESHOLD)

    def test_safe_state(self):
        """Test system stays safe with low values"""
        telemetry = {
            'tyres': 20,
            'driver_fatigue': 25,
            'thermal': 30,
            'hydraulics': 15,
            'brakes': 20,
            'fuel_system': 10,
            'timestamp': 5
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        self.assertFalse(pit_triggered)
        self.assertIn('SAFE', status)
        self.assertLess(hdi, CRITICAL_HDI_THRESHOLD)

    def test_hdi_calculation(self):
        """Test HDI calculation with known weights"""
        telemetry = {
            'tyres': 50,           # 50 * 0.25 = 12.5
            'driver_fatigue': 50,  # 50 * 0.25 = 12.5
            'thermal': 50,         # 50 * 0.20 = 10.0
            'hydraulics': 50,      # 50 * 0.15 = 7.5
            'brakes': 50,          # 50 * 0.10 = 5.0
            'fuel_system': 50,     # 50 * 0.05 = 2.5
            'timestamp': 10
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        # Expected HDI = 50 (all params at 50, weights sum to 1.0)
        self.assertAlmostEqual(hdi, 50.0, places=1)

    def test_weights_sum_to_one(self):
        """Verify weights sum to exactly 1.0"""
        total_weight = sum(WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)


class TestGraniteAnalysis(unittest.TestCase):
    """Test IBM Granite LLM Analysis Functions"""

    def test_granite_critical_assessment(self):
        """Test Granite assessment for critical state"""
        telemetry = {
            'tyres': 45,
            'driver_fatigue': 88,
            'thermal': 50,
            'hydraulics': 20,
            'brakes': 30,
            'fuel_system': 15,
            'timestamp': 28
        }
        analysis = generate_granite_analysis(telemetry, 50.0, True, 'BIOLOGICAL VETO')

        self.assertEqual(analysis['system_health'], 'CRITICAL - IMMEDIATE INTERVENTION REQUIRED')
        self.assertTrue(len(analysis['risk_factors']) > 0)
        self.assertTrue(len(analysis['recommendations']) > 0)

    def test_granite_nominal_assessment(self):
        """Test Granite assessment for nominal state"""
        telemetry = {
            'tyres': 20,
            'driver_fatigue': 25,
            'thermal': 30,
            'hydraulics': 15,
            'brakes': 20,
            'fuel_system': 10,
            'timestamp': 5
        }
        analysis = generate_granite_analysis(telemetry, 22.0, False, 'SAFE')

        self.assertEqual(analysis['system_health'], 'NOMINAL - WITHIN SAFE PARAMETERS')
        self.assertEqual(len(analysis['risk_factors']), 0)

    def test_granite_warning_assessment(self):
        """Test Granite assessment for warning state"""
        telemetry = {
            'tyres': 65,
            'driver_fatigue': 65,
            'thermal': 65,
            'hydraulics': 65,
            'brakes': 65,
            'fuel_system': 65,
            'timestamp': 20
        }
        analysis = generate_granite_analysis(telemetry, 65.0, False, 'WARNING')

        self.assertEqual(analysis['system_health'], 'WARNING - MONITORING REQUIRED')

    def test_granite_explanation_generation(self):
        """Test natural language explanation generation"""
        telemetry = {
            'tyres': 45,
            'driver_fatigue': 88,
            'thermal': 50,
            'hydraulics': 20,
            'brakes': 30,
            'fuel_system': 15,
            'timestamp': 28
        }
        analysis = generate_granite_analysis(telemetry, 50.0, True, 'BIOLOGICAL VETO: FATIGUE')

        self.assertIsNotNone(analysis['explanation'])
        self.assertIn('System Status', analysis['explanation'])
        self.assertIn('HDI Score', analysis['explanation'])

    def test_granite_parameter_recommendations(self):
        """Test specific parameter-based recommendations"""
        telemetry = {
            'tyres': 88,  # High tire degradation
            'driver_fatigue': 25,
            'thermal': 30,
            'hydraulics': 15,
            'brakes': 20,
            'fuel_system': 10,
            'timestamp': 15
        }
        analysis = generate_granite_analysis(telemetry, 45.0, False, 'WARNING')

        # Should generate tire-related recommendations
        tire_recs = [r for r in analysis['recommendations'] if 'tyre' in r.lower()]
        self.assertTrue(len(tire_recs) > 0)


class TestSafetyThresholds(unittest.TestCase):
    """Test Safety Threshold Boundaries"""

    def test_redline_veto_boundary(self):
        """Test behavior at Redline Veto boundary"""
        # Exactly at threshold
        telemetry_at = {
            'tyres': 85,
            'driver_fatigue': 50,
            'thermal': 50,
            'hydraulics': 50,
            'brakes': 50,
            'fuel_system': 50,
            'timestamp': 10
        }
        pit1, _, _ = ibm_granite_decision_engine(telemetry_at)

        # Just below threshold
        telemetry_below = {
            'tyres': 84,
            'driver_fatigue': 50,
            'thermal': 50,
            'hydraulics': 50,
            'brakes': 50,
            'fuel_system': 50,
            'timestamp': 10
        }
        pit2, _, _ = ibm_granite_decision_engine(telemetry_below)

        self.assertTrue(pit1)
        self.assertFalse(pit2)

    def test_cascading_failure_boundary(self):
        """Test behavior at Cascading Failure boundary"""
        # Just above threshold
        telemetry_above = {
            'tyres': 70.5,
            'driver_fatigue': 70.5,
            'thermal': 70.5,
            'hydraulics': 70.5,
            'brakes': 70.5,
            'fuel_system': 70.5,
            'timestamp': 20
        }
        pit1, _, hdi1 = ibm_granite_decision_engine(telemetry_above)

        # Just below threshold
        telemetry_below = {
            'tyres': 69,
            'driver_fatigue': 69,
            'thermal': 69,
            'hydraulics': 69,
            'brakes': 69,
            'fuel_system': 69,
            'timestamp': 20
        }
        pit2, _, hdi2 = ibm_granite_decision_engine(telemetry_below)

        self.assertTrue(hdi1 >= CRITICAL_HDI_THRESHOLD)
        self.assertFalse(hdi2 >= CRITICAL_HDI_THRESHOLD)


class TestEdgeCases(unittest.TestCase):
    """Test Edge Cases and Failure Scenarios"""

    def test_all_parameters_critical(self):
        """Test when all parameters are at critical level"""
        telemetry = {
            'tyres': 90,
            'driver_fatigue': 90,
            'thermal': 90,
            'hydraulics': 90,
            'brakes': 90,
            'fuel_system': 90,
            'timestamp': 25
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        self.assertTrue(pit_triggered)
        self.assertEqual(hdi, 90)

    def test_all_parameters_perfect(self):
        """Test perfect system state"""
        telemetry = {
            'tyres': 0,
            'driver_fatigue': 0,
            'thermal': 0,
            'hydraulics': 0,
            'brakes': 0,
            'fuel_system': 0,
            'timestamp': 1
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        self.assertFalse(pit_triggered)
        self.assertEqual(hdi, 0)

    def test_mixed_critical_and_safe(self):
        """Test mix of critical and safe parameters"""
        telemetry = {
            'tyres': 90,      # Critical
            'driver_fatigue': 20,  # Safe
            'thermal': 90,    # Critical
            'hydraulics': 20, # Safe
            'brakes': 20,     # Safe
            'fuel_system': 20, # Safe
            'timestamp': 15
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        # HDI should be weighted average
        expected_hdi = (90*0.25 + 20*0.25 + 90*0.20 + 20*0.15 + 20*0.10 + 20*0.05)
        self.assertAlmostEqual(hdi, expected_hdi, places=1)

    def test_single_parameter_spike(self):
        """Test single parameter spike amid normal conditions"""
        telemetry = {
            'tyres': 25,
            'driver_fatigue': 25,
            'thermal': 88,    # Spike to critical
            'hydraulics': 25,
            'brakes': 25,
            'fuel_system': 25,
            'timestamp': 12
        }
        pit_triggered, status, hdi = ibm_granite_decision_engine(telemetry)
        self.assertTrue(pit_triggered)
        self.assertIn('THERMAL', status.upper())


if __name__ == '__main__':
    unittest.main(verbosity=2)
