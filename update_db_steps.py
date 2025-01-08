# Updating DB

from django.db.models import Q
from instagram.models import Account
from instagram.models import Account, Message, Thread

Account.objects.filter(
    Q(status_param="Closing the Sale")
).update(status_param="Sales Qualified")

Account.objects.filter(
    Q(status_param="Rapport Building") | Q(status_param="Needs Assessment")
).update(status_param="Prequalified")

Account.objects.filter(
    Q(status_param="Solution Presentation")
).update(status_param="Sales Qualified")

Account.objects.filter(
    Q(status_param="")
).update(status_param="Prequalified")

Account.objects.filter(
    Q(status_param__isnull=True)
).update(status_param="Prequalified")

Account.objects.filter(
    Q(status_param="['DEFERRED - 24']")
).update(status_param="Prequalified")

Account.objects.filter(
    Q(status_param="['IDENTIFIED OBJECTION - Switching System Headaches']")
).update(status_param="Sales Qualified")

Account.objects.filter(
    Q(status_param= "['IDENTIFIED OBJECTION - cost concern']")
).update(status_param="Sales Qualified")  

Account.objects.filter(
    Q(status_param= "high_potential")
).update(status_param="Sales Qualified")  

Account.objects.filter(
    Q(status_param= "unknown")
).update(status_param="Prequalified")  

Account.objects.filter(
    Q(status_param= "Sales Qualified Lead")
).update(status_param="Sales Qualified")  

Account.objects.filter(
    Q(status_param= "Human takeover")
).update(status_param="Sales Qualified") 




from django.db.models import Count
from django.db import transaction
from instagram.models import Account, Thread, OutSourced, OutreachTime, Photo

def merge_duplicate_accounts():
    # Find duplicate igname values
    duplicate_ignames = (
        Account.objects.values('igname')
        .annotate(count=Count('id'))  # Use Count from django.db.models
        .filter(count__gt=1)
    )

    for duplicate in duplicate_ignames:
        igname = duplicate['igname']
        accounts = list(Account.objects.filter(igname=igname))
        
        if len(accounts) > 1:
            main_account = accounts[0]
            other_accounts = accounts[1:]

            with transaction.atomic():  # Ensure atomicity
                print(f"Merging accounts for igname: {igname}")
                # Update main account details
                for account in other_accounts:
                    main_account.full_name = main_account.full_name or account.full_name
                    main_account.email = main_account.email or account.email
                    main_account.phone_number = main_account.phone_number or account.phone_number
                    main_account.profile_url = main_account.profile_url or account.profile_url
                    main_account.script_score = main_account.script_score or account.script_score
                    main_account.script_version = main_account.script_version or account.script_version
                    main_account.confirmed_problems += f", {account.confirmed_problems}"
                    main_account.rejected_problems += f", {account.rejected_problems}"
                    main_account.notes = (main_account.notes or "") + (account.notes or "")

                # Save updates to the main account
                main_account.save()

                # Relink related models to main_account
                Thread.objects.filter(account__in=other_accounts).update(account=main_account)
                OutSourced.objects.filter(account__in=other_accounts).update(account=main_account)
                OutreachTime.objects.filter(account_to_be_assigned__in=other_accounts).update(account_to_be_assigned=main_account)
                Photo.objects.filter(account__in=other_accounts).update(account=main_account)

                # Delete other duplicate accounts
                Account.objects.filter(id__in=[acc.id for acc in other_accounts]).delete()

                print(f"Merged {len(other_accounts)} accounts into {main_account.id}")
        else:
            print(f"No duplicates found for igname: {igname}")

    print("All duplicate accounts processed.")
