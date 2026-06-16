# Input Contract

## Purpose

This document defines the required inputs that must be present before a work unit or workflow stage may validly proceed.

## Contract Responsibilities

The input contract must define:

- required artifacts
- required decisions
- required upstream state
- required dependency satisfaction

## Universal Input Rule

A stage may not validly consume a work unit unless its declared prerequisites are present and sufficiently explicit.

## Work Unit Input Contracts

### Intent

Required inputs:

- objective or request
- initial scope
- constraints

Entry condition:

- enough information exists to evaluate whether work should become a program

### Program

Required inputs:

- accepted or overridable intent
- scope definition
- top-level constraints

Entry condition:

- the idea is eligible for program formation

### Module

Required inputs:

- parent program
- module objective
- relevant program constraints

Entry condition:

- module scope is concrete enough to decompose into phases and issues

### Phase

Required inputs:

- parent module
- phase objective
- issue grouping rationale

Entry condition:

- phase boundaries are meaningful and traceable to module scope

### Issue

Required inputs:

- parent phase and module context
- explicit scope
- explicit dependencies
- required inputs
- acceptance criteria

Entry condition:

- issue is defined well enough to become planned and eventually ready

### Proof

Required inputs:

- executed issue work
- evidence sources
- mapped acceptance criteria

Entry condition:

- work has progressed far enough to support evidence collection

### Review

Required inputs:

- subject artifact
- proof artifact
- applicable completion criteria

Entry condition:

- the subject is reviewable and evidence exists

### Integration

Required inputs:

- subject artifact
- passing review
- integration scope and downstream context

Entry condition:

- review verdict is pass

## Ownership Rule

The producer is responsible for providing valid inputs to the next stage.

The consumer is responsible for rejecting handoff if required inputs are incomplete or invalid.

## Read Next

1. `OUTPUT-CONTRACT.md`
2. `VALIDATION-CONTRACT.md`
