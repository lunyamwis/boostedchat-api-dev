#!/bin/bash

# Step 1: Log into the Docker container and run the following commands
python manage.py shell -c "
from sales_rep.models import SalesRep
try:
    srep = SalesRep.objects.get(ig_username='barbersince98')
    srep.available = False
    srep.save()
    print(f'SalesRep {srep.ig_username} is now unavailable.')
except SalesRep.DoesNotExist:
    print('SalesRep with ig_username=barbersince98 does not exist.')
"