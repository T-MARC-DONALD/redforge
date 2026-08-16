"""redforge.core - the attack engine.

Sub-packages/modules that will live here as we build:
    models.py       - shared dataclasses (Turn, Evaluation, AttackResult, ...)
    base_attack.py  - the abstract attack class every attack inherits from
    registry.py     - auto-discovers attack modules
    scorer.py       - judges whether a response means the attack succeeded
    runner.py       - orchestrates attacks against a target
    sequencer.py    - multi-turn attack sequencing (the key differentiator)
"""
