import unittest

from elfcalc import ArithmeticMachine, Instruction, MachineError


class ArithmeticMachineTests(unittest.TestCase):
    def test_all_four_operations(self):
        machine = ArithmeticMachine([12, 3])
        self.assertEqual(machine.execute(Instruction(2, 0, "+", 1)), 15)
        self.assertEqual(machine.execute(Instruction(3, 0, "-", 1)), 9)
        self.assertEqual(machine.execute(Instruction(4, 0, "*", 1)), 36)
        self.assertEqual(machine.execute(Instruction(5, 0, "/", 1)), 4)
        self.assertEqual(machine.instruction_count, 4)

    def test_destination_is_overwritten(self):
        machine = ArithmeticMachine([7, 5])
        self.assertEqual(machine.execute(Instruction(0, 0, "-", 1)), 2)
        self.assertEqual(machine.registers[0], 2)

    def test_division_must_be_exact(self):
        machine = ArithmeticMachine([7, 2])
        with self.assertRaisesRegex(MachineError, "exact"):
            machine.execute(Instruction(2, 0, "/", 1))

    def test_division_by_zero_is_rejected(self):
        machine = ArithmeticMachine([7, 0], require_positive=False)
        with self.assertRaisesRegex(MachineError, "zero"):
            machine.execute(Instruction(2, 0, "/", 1))

    def test_uninitialized_register_is_rejected(self):
        machine = ArithmeticMachine([2, 3])
        with self.assertRaisesRegex(MachineError, "uninitialized"):
            machine.execute(Instruction(4, 0, "+", 3))

    def test_value_limit_is_enforced(self):
        machine = ArithmeticMachine([11, 11], value_limit=100)
        with self.assertRaisesRegex(MachineError, "value_limit"):
            machine.execute(Instruction(2, 0, "*", 1))

    def test_positive_result_constraint_is_enforced(self):
        machine = ArithmeticMachine([2, 5])
        with self.assertRaisesRegex(MachineError, "positive"):
            machine.execute(Instruction(2, 0, "-", 1))

    def test_targets_are_tracked_even_if_register_is_overwritten(self):
        machine = ArithmeticMachine([2, 3])
        machine.execute(Instruction(2, 0, "+", 1))
        machine.execute(Instruction(2, 0, "*", 1))
        self.assertTrue(machine.contains_all([2, 3, 5, 6]))

    def test_register_bank_is_fixed_at_48(self):
        machine = ArithmeticMachine([1])
        self.assertEqual(len(machine.registers), 48)
        with self.assertRaises(MachineError):
            machine.execute(Instruction(48, 0, "+", 0))

    def test_program_execution(self):
        machine = ArithmeticMachine([2, 3])
        machine.run([
            Instruction(2, 0, "+", 1),
            Instruction(3, 2, "*", 1),
        ])
        self.assertEqual(machine.registers[3], 15)


if __name__ == "__main__":
    unittest.main()
