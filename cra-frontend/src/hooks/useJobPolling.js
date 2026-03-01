/**
 * hooks/useJobPolling.js
 * Polls /api/jobs/:id every 2 seconds until terminal state.
 */
import { useState, useEffect, useRef } from 'react'
import { getJobStatus } from '../api/client'

const TERMINAL = ['completed', 'failed']

export function useJobPolling(jobId, onDone) {
  const [job, setJob]       = useState(null)
  const [error, setError]   = useState(null)
  const intervalRef         = useRef(null)

  useEffect(() => {
    if (!jobId) return
    setJob(null)
    setError(null)

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId)
        setJob(data)
        if (TERMINAL.includes(data.status)) {
          clearInterval(intervalRef.current)
          onDone?.(data)
        }
      } catch (err) {
        setError(err.message)
        clearInterval(intervalRef.current)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2000)
    return () => clearInterval(intervalRef.current)
  }, [jobId])   // eslint-disable-line react-hooks/exhaustive-deps

  return { job, error }
}
