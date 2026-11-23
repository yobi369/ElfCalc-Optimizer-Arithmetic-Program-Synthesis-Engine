import unittest

from elfcalc.target_dna import analyze_targets, fingerprint


class TargetDNATests(unittest.TestCase):
    def test_fingerprint_is_deterministic(self):
        self.assertEqual(fingerprint(84), fingerprint(84))
        self.assertEqual(fingerprint(84).residues[:3], (0, 4, 0))
        self.assertEqual(fingerprint(84).parity, 0)

    def test_rejects_nonpositive_values(self):
        with self.assertRaises(ValueError):
            fingerprint(0)
        with self.assertRaises(ValueError):
            analyze_targets([2, -3], [5], 100)

    def test_discovers_gcd_difference_and_quotient_candidates(self):
        dna = analyze_targets([12, 18], [6, 30], 100)
        self.assertIn(6, dna.candidate_intermediates)
        self.assertIn(2, dna.candidate_intermediates)
        self.assertIn(3, dna.candidate_intermediates)

    def test_relations_are_exact_and_bounded(self):
        dna = analyze_targets([2, 3], [5, 6], 6)
        edges = {(e.left, e.operator, e.right, e.result) for e in dna.relations}
        self.assertIn((2, "+", 3, 5), edges)
        self.assertIn((2, "*", 3, 6), edges)
        self.assertNotIn((3, "*", 5, 15), edges)

    def test_results_are_sorted_and_deduplicated(self):
        dna = analyze_targets([3, 2, 3], [6, 5, 6], 100)
        self.assertEqual(dna.candidate_intermediates, tuple(sorted(set(dna.candidate_intermediates))))
        self.assertEqual(dna.relations, tuple(sorted(
            set(dna.relations),
            key=lambda e: (e.result, e.operator, e.left, e.right),
        )))


if __name__ == "__main__":
    unittest.main()
