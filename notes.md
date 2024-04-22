# Notes

## Check the number of Sent Tasks
```bash
docker compose logs api | grep "Sending due task SendFirstCompliment" | wc -l # assumes logs are only available for `today`
```

## Checking failed tasks