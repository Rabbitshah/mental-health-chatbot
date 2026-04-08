# Backend Tests

This directory contains property-based and unit tests for the mental health chatbot backend.

## Setup

Install test dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run only property tests:
```bash
pytest -m property
```

Run specific test file:
```bash
pytest tests/test_property_cascade_deletion.py
```

Run with verbose output:
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_property_cascade_deletion.py` - Property tests for database cascade deletion and message ordering

## Property-Based Testing

Property tests use [Hypothesis](https://hypothesis.readthedocs.io/) to generate test cases automatically. These tests validate universal properties that should hold for all inputs:

- **Property 7: Message Retrieval Ordering** - Messages are always retrieved in chronological order
- **Cascade Deletion Properties** - Deleting users/sessions properly cascades to related data

## Test Database

Tests use an in-memory SQLite database that is created and destroyed for each test function, ensuring test isolation.
