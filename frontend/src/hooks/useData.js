import { useState, useEffect, useCallback, useRef } from "react";
import { pipelineAPI, analyticsAPI, healthAPI } from "../utils/api";

export function usePipelines(pollInterval = 5000) {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetch = useCallback(async () => {
    try {
      const data = await pipelineAPI.list({ limit: 50 });
      setPipelines(data.runs || []);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    if (pollInterval) {
      timerRef.current = setInterval(fetch, pollInterval);
    }
    return () => clearInterval(timerRef.current);
  }, [fetch, pollInterval]);

  return { pipelines, loading, error, refetch: fetch };
}

export function useAnalytics(pollInterval = 8000) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetch = useCallback(async () => {
    try {
      const data = await analyticsAPI.summary();
      setAnalytics(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    if (pollInterval) {
      timerRef.current = setInterval(fetch, pollInterval);
    }
    return () => clearInterval(timerRef.current);
  }, [fetch, pollInterval]);

  return { analytics, loading, error, refetch: fetch };
}

export function usePipelineDetail(runId) {
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    pipelineAPI
      .get(runId)
      .then((data) => {
        setRun(data);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [runId]);

  return { run, loading, error };
}

export function useHealth(pollInterval = 15000) {
  const [health, setHealth] = useState(null);
  const timerRef = useRef(null);

  const check = useCallback(async () => {
    try {
      const data = await healthAPI.check();
      setHealth(data);
    } catch {
      setHealth({ status: "unhealthy", database: "disconnected" });
    }
  }, []);

  useEffect(() => {
    check();
    timerRef.current = setInterval(check, pollInterval);
    return () => clearInterval(timerRef.current);
  }, [check, pollInterval]);

  return health;
}
