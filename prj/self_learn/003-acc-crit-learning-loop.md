# Acceptance Criteria: Learning loop automation

## R3.1: Cycle structure
- [ ] Learning cycle function exists
- [ ] Cycle has 4 phases: observe, update, verify, reuse
- [ ] Each phase is a separate function

## R3.2: Observe phase
- [ ] Can query relevant memory for context
- [ ] Returns structured observation data
- [ ] Identifies gaps and opportunities

## R3.3: Update phase
- [ ] Can propose a change
- [ ] Can apply the change to database or file system
- [ ] Creates reasoning episode record

## R3.4: Verify phase
- [ ] Can compare before/after state
- [ ] Returns verification result
- [ ] Records evidence of improvement

## R3.5: Reuse phase
- [ ] Can identify reusable pattern
- [ ] Stores pattern in appropriate table
- [ ] Pattern can be retrieved later

## R3.6: Audit trail
- [ ] Each step creates journal entry
- [ ] Reasoning episode is created
- [ ] Changes are reversible (not lost)