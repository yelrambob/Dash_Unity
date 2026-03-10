# [LATER]
# Runs a single patient through a scanner.
# Verify scan timer, cooldown, and state transitions.
# Run from project root: python tests/test_scanner.py

# TODO: create one Scanner, one Patient with one exam,
#       call scanner_manager.try_assign(), then tick until IDLE,
#       assert state sequence is correct
