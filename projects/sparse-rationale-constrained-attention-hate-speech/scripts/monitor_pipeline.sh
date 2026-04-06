#!/bin/bash
# Monitor Wave 1 jobs and continue pipeline when complete

set -euo pipefail

WAVE1_JOBS=(11464115 11464117)
MAX_WAIT=432000  # 5 days in seconds
POLL_INTERVAL=300  # 5 minutes

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

wait_for_jobs() {
    local job_ids=("$@")
    local start_time=$(date +%s)

    while true; do
        local completed=0
        local failed=0
        local running=0

        for job_id in "${job_ids[@]}"; do
            # Check if job is in queue
            if squeue -j "$job_id" -h | grep -q .; then
                # Job is running or pending
                running=$((running + 1))
            else
                # Job is not in queue, check exit status
                if sacct -j "$job_id" -p | grep -q COMPLETED; then
                    completed=$((completed + 1))
                elif sacct -j "$job_id" -p | grep -q "FAILED\|TIMEOUT"; then
                    failed=$((failed + 1))
                    log "ERROR: Job $job_id failed or timed out"
                fi
            fi
        done

        local elapsed=$(($(date +%s) - start_time))
        log "Status: $completed completed, $failed failed, $running running (elapsed: ${elapsed}s)"

        if [[ $((completed + failed)) -eq ${#job_ids[@]} ]]; then
            if [[ $failed -gt 0 ]]; then
                log "FATAL: Some jobs failed"
                return 1
            else
                log "SUCCESS: All Wave 1 jobs completed"
                return 0
            fi
        fi

        if [[ $elapsed -gt $MAX_WAIT ]]; then
            log "FATAL: Timeout waiting for jobs"
            return 1
        fi

        sleep $POLL_INTERVAL
    done
}

main() {
    log "=== Pipeline Monitor ==="
    log "Waiting for Wave 1 jobs to complete: ${WAVE1_JOBS[*]}"

    if wait_for_jobs "${WAVE1_JOBS[@]}"; then
        log "Wave 1 complete! Next steps:"
        log "  1. Verify Wave 1 outputs"
        log "  2. Submit Wave 2 jobs"
        log "  3. Run analysis phases"
        exit 0
    else
        log "Pipeline failed"
        exit 1
    fi
}

main "$@"
