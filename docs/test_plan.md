# Unit Tests - TDD Skeleton

## Naming
Pattern `should_[result]_when_[condition]`.

## Cases
- should_return_structured_report_when_documents_loaded
- should_flag_date_conflict_when_motion_differs_from_police_report
- should_not_crash_when_input_contains_sql_injection_payload
- should_return_empty_list_when_input_is_null_equivalent
- should_mark_quote_as_could_not_verify_when_source_not_found
- should_mark_authority_as_could_not_verify_when_case_text_missing
- should_handle_oversized_payload_when_motion_is_very_large

## AAA Criteria
- Arrange: load synthetic text fixtures.
- Act: execute target agent/service.
- Assert: validate one primary outcome per test.
