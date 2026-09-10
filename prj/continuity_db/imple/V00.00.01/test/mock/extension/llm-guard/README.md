# Mock llm-guard

Deterministic test doubles for the optional `llm-guard` adapter.

This directory deliberately contains no dependency on the real `llm-guard`
package and never downloads models. Load `llm_guard_mock.py` by path or add
this directory to a test's import path when testing the content-guard adapter.
