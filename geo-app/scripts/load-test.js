import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up
    { duration: '1m', target: 50 },     // Sustained load
    { duration: '30s', target: 100 },   // Peak
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% under 2s
    http_req_failed: ['rate<0.05'],      // <5% errors
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, { 'health status 200': (r) => r.status === 200 });

  // Heatmap (most common request)
  const heatmapRes = http.get(`${BASE_URL}/predictions/heatmap?limit=100`);
  check(heatmapRes, {
    'heatmap status 200': (r) => r.status === 200,
    'heatmap has points': (r) => JSON.parse(r.body).points.length > 0,
  });

  // Stats by city
  const statsRes = http.get(`${BASE_URL}/predictions/stats-by-city`);
  check(statsRes, { 'stats status 200': (r) => r.status === 200 });

  // Nearby predictions
  const nearbyRes = http.get(`${BASE_URL}/predictions/nearby?lat=20.67&lon=-103.35&radius_km=2&limit=10`);
  check(nearbyRes, { 'nearby status 200': (r) => r.status === 200 });

  sleep(1);
}
