# Operations Runbook - NL-FHIR Production

**Production Readiness Score: 10/10 ✅**

## Quick Reference

### Emergency Contacts
- **On-Call Engineer:** Refer to PagerDuty rotation
- **System Health:** `http://your-domain.com/health`
- **Metrics:** `http://your-domain.com/metrics/prometheus`
- **Logs:** `/app/logs/` or `docker logs nl-fhir-production`

### Critical Endpoints
| Endpoint | Purpose | Expected Response Time |
|----------|---------|----------------------|
| `/health` | Overall health | < 100ms |
| `/ready` | Readiness probe | < 50ms |
| `/live` | Liveness probe | < 50ms |
| `/convert` | FHIR conversion | < 2s (P95) |
| `/validate` | Bundle validation | < 1s |
| `/metrics/prometheus` | Monitoring data | < 200ms |

---

## Common Operational Scenarios

### Scenario 1: High Response Times

**Symptoms:**
- `/convert` endpoint > 2s response time
- P95 latency above SLA
- User complaints about slowness

**Diagnosis:**
```bash
# Check current response times
curl -w "@curl-format.txt" http://localhost:8001/convert

# Check Prometheus metrics
curl http://localhost:8001/metrics/prometheus | grep duration

# Check system resources
docker stats nl-fhir-production

# Check HAPI FHIR connectivity
curl http://localhost:8081/fhir/metadata
```

**Resolution Steps:**
1. **Check HAPI FHIR:** If HAPI is slow, app will be slow
   ```bash
   # Test HAPI directly
   time curl http://localhost:8081/fhir/metadata
   
   # If slow, restart HAPI
   docker restart hapi-fhir-production
   ```

2. **Check CPU/Memory:**
   ```bash
   # If high CPU/memory usage
   docker stats nl-fhir-production
   
   # Increase resources if needed
   docker-compose -f docker-compose.prod.yml down
   # Edit docker-compose.prod.yml to increase limits
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Check Worker Count:**
   ```bash
   # Increase Gunicorn workers if needed
   # Workers = (2 * CPU cores) + 1
   export WORKERS=9
   docker-compose -f docker-compose.prod.yml restart nl-fhir
   ```

4. **Check Logs for Errors:**
   ```bash
   docker logs --tail 100 nl-fhir-production | grep ERROR
   ```

**Prevention:**
- Monitor P95 latency daily
- Set up alerts for > 1.5s response times
- Auto-scale based on load

---

### Scenario 2: Service Down / Not Responding

**Symptoms:**
- 503 Service Unavailable
- Health check failures
- Container not running

**Diagnosis:**
```bash
# Check container status
docker ps -a | grep nl-fhir

# Check container logs
docker logs --tail 50 nl-fhir-production

# Check application health
curl http://localhost:8001/health
```

**Resolution Steps:**

1. **Container Crashed:**
   ```bash
   # Check why it stopped
   docker logs nl-fhir-production
   
   # Restart container
   docker start nl-fhir-production
   
   # If that fails, recreate
   docker-compose -f docker-compose.prod.yml up -d --force-recreate nl-fhir
   ```

2. **Application Error at Startup:**
   ```bash
   # Check logs for errors
   docker logs nl-fhir-production 2>&1 | grep -i error
   
   # Common issues:
   # - Missing environment variables
   # - Model download failure
   # - Port already in use
   
   # Fix and restart
   docker-compose -f docker-compose.prod.yml restart nl-fhir
   ```

3. **Out of Memory:**
   ```bash
   # Check if OOM killed
   docker inspect nl-fhir-production | grep OOMKilled
   
   # If true, increase memory limit
   # Edit docker-compose.prod.yml:
   # services.nl-fhir.deploy.resources.limits.memory: 8G
   
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Prevention:**
- Enable auto-restart: `restart: unless-stopped`
- Monitor memory usage
- Set up alerts for container stops

---

### Scenario 3: HAPI FHIR Connection Issues

**Symptoms:**
- Validation failures
- `/validate` endpoint returning errors
- "HAPI FHIR unavailable" in logs

**Diagnosis:**
```bash
# Test HAPI connectivity
curl http://localhost:8081/fhir/metadata

# Check HAPI container
docker ps | grep hapi

# Check HAPI logs
docker logs hapi-fhir-production --tail 50
```

**Resolution Steps:**

1. **HAPI Container Down:**
   ```bash
   # Restart HAPI
   docker start hapi-fhir-production
   
   # Or recreate
   docker-compose -f docker-compose.prod.yml up -d hapi-fhir
   ```

2. **HAPI Slow/Unresponsive:**
   ```bash
   # Restart HAPI
   docker restart hapi-fhir-production
   
   # Wait for health check
   sleep 30
   curl http://localhost:8081/fhir/metadata
   ```

3. **Network Issues:**
   ```bash
   # Check network connectivity
   docker network inspect nl-fhir-network
   
   # Test from within nl-fhir container
   docker exec nl-fhir-production curl http://hapi-fhir:8080/fhir/metadata
   
   # If network broken, recreate
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Graceful Degradation:**
- App will fall back to local validation if HAPI unavailable
- This is expected behavior
- Monitor Prometheus metric: `nl_fhir_hapi_server_available`

**Prevention:**
- Monitor HAPI health: `/fhir/metadata`
- Set up alerts for HAPI downtime
- Consider HAPI failover/redundancy

---

### Scenario 4: High Error Rate

**Symptoms:**
- Prometheus shows increasing error count
- 500 Internal Server Error responses
- Exception traces in logs

**Diagnosis:**
```bash
# Check error metrics
curl http://localhost:8001/metrics/prometheus | grep errors_total

# Check recent errors in logs
docker logs --since 10m nl-fhir-production | grep ERROR

# Check specific error types
docker logs nl-fhir-production | grep -A 5 "Traceback"
```

**Resolution Steps:**

1. **Identify Error Type:**
   ```bash
   # Group errors by type
   docker logs nl-fhir-production | grep ERROR | sort | uniq -c
   ```

2. **Common Error Types:**

   **NLP Model Errors:**
   ```bash
   # Reload NLP models
   docker restart nl-fhir-production
   ```

   **FHIR Validation Errors:**
   ```bash
   # Check if HAPI is responding
   curl http://localhost:8081/fhir/metadata
   
   # Restart if needed
   docker restart hapi-fhir-production
   ```

   **Memory Errors:**
   ```bash
   # Check memory usage
   docker stats nl-fhir-production
   
   # Increase if needed (edit docker-compose.prod.yml)
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Code Bugs:**
   ```bash
   # Collect error details
   docker logs nl-fhir-production > error-log-$(date +%Y%m%d-%H%M%S).txt
   
   # Create incident ticket
   # Rollback if necessary:
   docker pull your-registry.com/nl-fhir:previous-version
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Prevention:**
- Monitor error rate in Prometheus
- Set alerts for > 1% error rate
- Implement retry logic for transient errors

---

### Scenario 5: Security Alert / Vulnerability

**Symptoms:**
- Bandit or Safety report shows new vulnerability
- Security scan failure in CI/CD
- CVE notification

**Immediate Actions:**
```bash
# Run security scan
uv run bandit -r src/nl_fhir/ -ll

# Check dependencies
uv run safety check

# Review findings
cat bandit-report.json
```

**Resolution Steps:**

1. **Assess Severity:**
   - **CRITICAL/HIGH:** Immediate action required
   - **MEDIUM:** Fix within 24-48 hours
   - **LOW:** Fix in next release

2. **Update Dependencies:**
   ```bash
   # Update vulnerable package
   # Edit pyproject.toml with new version
   uv sync
   
   # Test thoroughly
   uv run pytest
   
   # Deploy
   ./scripts/docker-prod-build.sh
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Code Fix Required:**
   ```bash
   # Fix the code issue
   # Run security scan again
   uv run bandit -r src/nl_fhir/ -ll
   
   # Commit with security tag
   git commit -m "security: Fix vulnerability CVE-XXXX"
   
   # Deploy immediately for CRITICAL/HIGH
   ```

**Prevention:**
- Pre-commit hooks run Bandit automatically
- CI/CD runs Security scan stage
- Regular dependency updates
- Subscribe to security advisories

---

## Monitoring & Alerts

### Key Metrics to Monitor

**Application Health:**
- `nl_fhir_app_healthy` - Should be 1
- `nl_fhir_hapi_server_available` - Should be 1

**Performance:**
- `nl_fhir_http_request_duration_seconds` (P95) - Should be < 2s
- `nl_fhir_conversions_total{status="failed"}` - Should be < 5% of total

**System Resources:**
- `nl_fhir_system_cpu_usage_percent` - Should be < 80%
- `nl_fhir_system_memory_usage_bytes` - Monitor trends

**Errors:**
- `nl_fhir_errors_total` - Should be minimal
- Rate of increase - Should be flat

### Recommended Alerts

**Critical (PagerDuty):**
```promql
# Service down
nl_fhir_app_healthy == 0

# High error rate
rate(nl_fhir_errors_total[5m]) > 10

# Response time SLA breach
histogram_quantile(0.95, rate(nl_fhir_http_request_duration_seconds_bucket[5m])) > 2
```

**Warning (Slack/Email):**
```promql
# HAPI unavailable
nl_fhir_hapi_server_available == 0

# High CPU
nl_fhir_system_cpu_usage_percent > 80

# Conversion failure rate
rate(nl_fhir_conversions_total{status="failed"}[10m]) / rate(nl_fhir_conversions_total[10m]) > 0.05
```

---

## Maintenance Windows

### Planned Maintenance

**Pre-Maintenance:**
```bash
# 1. Notify users (if applicable)
# 2. Create backup
docker exec nl-fhir-production tar -czf /tmp/backup.tar.gz /app/

# 3. Scale up temporarily (if doing rolling update)
# 4. Take snapshot of metrics
curl http://localhost:8001/metrics/prometheus > metrics-before.txt
```

**During Maintenance:**
```bash
# Perform updates
docker pull your-registry.com/nl-fhir:latest
docker-compose -f docker-compose.prod.yml up -d

# Wait for health
sleep 30
curl http://localhost:8001/health
```

**Post-Maintenance:**
```bash
# 1. Verify health
curl http://localhost:8001/health

# 2. Run smoke tests
uv run pytest -m smoke

# 3. Check metrics
curl http://localhost:8001/metrics/prometheus

# 4. Monitor for 30 minutes
# 5. Notify completion
```

### Emergency Maintenance

**Quick Rollback:**
```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Start previous version
docker run -d --name nl-fhir-production \
  -p 8001:8001 \
  your-registry.com/nl-fhir:previous-version

# Verify
curl http://localhost:8001/health
```

---

## Disaster Recovery

### Backup Strategy

**What to Backup:**
- Configuration files (`.env`, `docker-compose.prod.yml`)
- Custom modifications
- Logs (for audit trail)

**Backup Schedule:**
- Configuration: Before each deployment
- Logs: Daily rotation, keep 30 days

### Recovery Procedures

**Complete System Failure:**
```bash
# 1. Provision new infrastructure
# 2. Install Docker
# 3. Clone repository or pull from registry
git clone https://github.com/your-org/nl-fhir.git
cd nl-fhir

# 4. Restore configuration
cp /backup/.env .env
cp /backup/docker-compose.prod.yml docker-compose.prod.yml

# 5. Start services
./scripts/docker-prod-start.sh

# 6. Verify
curl http://localhost:8001/health

# RTO: < 15 minutes
# RPO: Latest deployment
```

---

## Support Escalation

**Level 1 - On-Call Engineer:**
- Restart services
- Check logs
- Follow runbook procedures

**Level 2 - Senior Engineer:**
- Code debugging
- Complex configuration issues
- Performance tuning

**Level 3 - Architect:**
- Architecture decisions
- Major incidents
- Security incidents

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-10-18  
**Production Readiness:** 10/10 ✅
