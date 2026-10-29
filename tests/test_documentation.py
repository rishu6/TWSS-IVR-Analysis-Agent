import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationGate(unittest.TestCase):
    def test_public_and_tenant_verification_are_distinct(self):
        matrix = (ROOT / 'docs/integration-capability-matrix.md').read_text()
        self.assertIn('not runtime or tenant verification', matrix)
        self.assertIn('Acefone India', matrix)
        self.assertIn('Cannot enumerate all duplicate', matrix)

    def test_mapping_does_not_claim_vendor_fields(self):
        mapping = (ROOT / 'docs/event-mapping.md').read_text()
        self.assertIn('not Acefone wire fields', mapping)
        self.assertIn('never merge', mapping)
