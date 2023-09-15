import math
import random

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.models import User
from data.helpers.random_data import get_random_compliment
from instagram.helpers.llm import query_gpt
from instagram.helpers.login import login_user
from instagram.models import Account, StatusCheck
from instagram.tasks import send_message

from .helpers.task_allocation import no_consecutives, no_more_than_x
from .models import SalesRep
from .serializers import AccountAssignmentSerializer, SalesRepSerializer

# Create your views here.


class SalesRepManager(viewsets.ModelViewSet):
    queryset = SalesRep.objects.all()
    serializer_class = SalesRepSerializer

    def get_serializer_class(self):
        if self.action == "assign_accounts":
            return AccountAssignmentSerializer

        return self.serializer_class

    def list(self, request):

        reps = SalesRep.objects.all()
        user_info = []
        for rep in reps:
            if User.objects.filter(id=rep.user.id).exists():
                info = {"user": User.objects.filter(id=rep.user.id).values(), "instagram": rep.instagram.values()}
                user_info.append(info)

        response = {"status_code": status.HTTP_200_OK, "info": user_info}
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="assign-accounts")
    def assign_accounts(self, request, pk=None):
        serializer = AccountAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instagram_accounts_ = []
        accounts = Account.objects.filter(Q(status=None) | ~Q(status__name="sent_first_compliment"))
        if accounts.exists():
            instagram_accounts_.append(accounts)

        print(accounts)
        instagram_accounts = []
        for accounts_ in instagram_accounts_:
            for account in accounts_:
                instagram_accounts.append(account.id)

        salesreps = list(SalesRep.objects.all())

        if len(salesreps) == 0:
            return Response({"message": "No sales reps"}, status=status.HTTP_400_BAD_REQUEST)

        ration = math.ceil(len(instagram_accounts) / len(salesreps))

        i = 0
        accounts_complimented = []

        while i < len(salesreps):
            allocations = random.choices(instagram_accounts, k=ration)

            if no_consecutives(allocations) and no_more_than_x(allocations):
                for j in range(ration):
                    if j > len(instagram_accounts):
                        break
                    account = get_object_or_404(Account, id=allocations[j])

                    salesreps[i].instagram.add(account)

                    statuscheck, _ = StatusCheck.objects.update_or_create(stage=1, name="sent_first_compliment")
                    account.status = statuscheck

                    account.save()
                    print(account.igname)
                    if account.igname:
                        if serializer.data.get("reaction") == 1:
                            cl = login_user(salesreps[i].ig_username, salesreps[i].ig_password)
                            user_id = cl.user_id_from_username(account.igname)
                            user_medias = cl.user_medias(user_id)

                            try:
                                media_id = cl.media_id(media_pk=user_medias[0].pk)
                                random_compliment = get_random_compliment(
                                    salesrep=salesreps[i], compliment_type="first_compliment"
                                )
                                comment = cl.media_comment(media_id, random_compliment)
                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "comment": comment.dict(),
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                            }
                            accounts_complimented.append(ready_accounts)
                        elif serializer.data.get("reaction") == 2:
                            first_compliment_prompt = """
                                Act as if you were an Instagram DM-based sales representative for the biggest beauty appointment management system & marketplace called Booksy. Recommend the personalized compliment to the US-based [get category from the data within the triple backticks] at the beginning of our Instagram DM-based conversation that will help establish the relationship and win the right to ask questions about their problems.
                                Each message needs to be a short DM message in a way that sounds natural and engaging, confirming that we believe that the[get category from the data within the triple backticks] is a great professional and we understand their point of view. make sure to use a tone of voice in line with those characteristics: "We’re revolutionizing the way people make appointments. [get category from the data within the triple backticks] are frustrated from wasting too much time managing their books when they could be focusing on their craft. Booksy offers a platform for them to streamline business management. Both a reliable receptionist and a trustworthy business partner, Booksy helps merchants grow and gives them time to master their skills. CONVERSATIONAL We are a business partner and friendly neighbor recommending a service or business. Our voice needs to match our attitude. Being corporate is too rigid, and can be alienating. Speaking casually and candidly allows customers to trust us. ENCOURAGING Our customers and merchants dream of fulfilling their full personal potential, and Booksy gives them the tools to accomplish that. GENUINE Booksy makes a promise to its customers. We’re adding a new meaning to their lives by redefining what it means to manage a business. How? By being accurate, honest, transparent, and receptive to customer feedback."
                                Possibly relevant information about the person you talk to & their business that you can use: ```{
                                "name": "styleseat",
                                "secondary_name": "Paul",
                                "logo_url": "background-image: url(\"https://d220aniogakg8b.cloudfront.net/static/uploads/2022/10/27/14984497_b0043943_200x200.jpg\");",
                                "profileUrl": "https://www.styleseat.com/m/v/barberpaul",
                                "category": "Barber",
                                "businessName": "Business name: The Fine Grooming Studio",
                                "ratings": "5.0\n(535)",
                                "serviceTitle": [
                                    "Mens Haircut and Shave",
                                    "",
                                    "Mens Haircut Only (No Shave)",
                                    "Mens Haircut and Shave",
                                    "Ultimate Grooming Package",
                                    "Men’s Grooming Package",
                                    "Men’s Haircut Only (No Shave)",
                                    "Mens Haircut and Shave",
                                    "Kids/Young Men  Haircut",
                                    "Hydrotherapy Bald Head Shave",
                                    "Clipper Line-up (Hair and/or Beard)",
                                    "Beard Line-up w/ Trim",
                                    "Beard Color w/ Line-up and Trim",
                                    "Hot Towel Shave (Face Only)",
                                    "Big Chop Men’s Haircut",
                                    "Women’s Clipper line-Up",
                                    "Womens Under Cut | Neck Trim",
                                    "Womens Haircut",
                                    "Womens Big Chop Haircut",
                                    "Eyebrow Arching",
                                    "Client Consultation",
                                    "Beard Therapy",
                                    "Hair Coloring",
                                    "DermaPore Facial Rejuvenation",
                                    "Detox Facial",
                                    "Purifying  Facial Rejuvenation",
                                    "Derma Scrub Shampoo and Conditioner",
                                    "Keloidalis Nuchae/Acne Treatment",
                                    "Derma Scrub Razor Bump Treatment",
                                    "House Calls",
                                    "Off Days/After/before Hours Haircuts"
                                ],
                                "serviceDetails": [
                                    "$55 and up for 45 minutes",
                                    "",
                                    "$50 and up for 45 minutes",
                                    "$65 and up for 60 minutes",
                                    "$175 and up for 90 minutes",
                                    "$75 and up for 60 minutes",
                                    "$40 and up for 45 minutes",
                                    "$55 and up for 45 minutes",
                                    "$35 and up for 30 minutes",
                                    "$65 and up for 45 minutes",
                                    "$25 and up for 30 minutes",
                                    "$35 and up for 30 minutes",
                                    "$50 and up for 60 minutes",
                                    "$50 and up for 30 minutes",
                                    "$75 and up for 60 minutes",
                                    "$25 and up for 15 minutes",
                                    "$40 and up for 30 minutes",
                                    "$50 and up for 45 minutes",
                                    "$75 and up for 60 minutes",
                                    "$12 and up for 15 minutes",
                                    "$25 and up for 15 minutes",
                                    "$50 and up for 45 minutes",
                                    "$50 and up for 60 minutes",
                                    "$65 and up for 45 minutes",
                                    "$55 and up for 45 minutes",
                                    "$45 and up for 45 minutes",
                                    "$30 and up for 15 minutes",
                                    "$250 and up for 120 minutes",
                                    "$40 and up for 45 minutes",
                                    "$150 and up for 90 minutes",
                                    "$100 and up for 60 minutes"
                                ],
                                "descriptionSection": [
                                    "This service includes any style of haircut, a shampoo and conditioning or a hot towel(optional). Ad...",
                                    "",
                                    "This service includes any style haircut. No shave is included. Add $10 extra for scissor haircuts.",
                                    "This service includes any style of haircut, a shampoo and conditioning or a hot towel(optional). Ad...\n6",
                                    "Any desired hairstyle, Beard Wash & Beard sculpting/trim Shampoo/Condition and Hot Towel, Eye B...\n6",
                                    "INCLUDES: Any desired hairstyle, Face Shave or Beard Trim and Lineup Shampoo/Conditioning and Hot T...\n6",
                                    "This service includes any style haircut. No shave is included. Add $10 extra for scissor haircuts.",
                                    "This service includes any style of haircut, a shampoo and conditioning or a hot towel(optional). Ad...\n6",
                                    "This service includes any style haircut. Add $10 extra for scissor cuts. Add $10 extra for a shave o...\n6",
                                    "This service Helps to even skin tone, reduce irritation and any inflammation. It detoxifies the por...\n6",
                                    "Clipper line-up for only the head or only the face with a razor finish. $15 for Kids. This service d...\n6",
                                    "This service includes the shaping of the beard. Price varies depending upon the length of the beard.",
                                    "This service includes a dry shave an permanent hair color enhancement of the beard. I will need to ...\n6",
                                    "This service includes a hot towel service along with a straight razor shave.",
                                    "The service is for men transitioning from a long hairstyle to a short natural haircut/hairstyle. It...\n6",
                                    "Clipper lineup only",
                                    "This service includes cutting the sides/neck only.",
                                    "This service includes any style haircut. (Shampoo and conditioning is optional).",
                                    "The service is for women transitioning from a long hairstyle to a short natural haircut/hairstyle. ...\n6",
                                    "Straight Razor finish",
                                    "This is for Haircut, Skin, Scalp, Color, and Consulting.",
                                    "This service includes a thorough shampoo/conditioning of the Beard, and beard buffing to give the be...\n6",
                                    "Highlighting and adding your desired color. This service may take more than 1 visit to get the desir...\n6",
                                    "Remove Black/Whiteheads from the nose and chin. Heating & Cooling sensation, Deep pore cleansing , ...\n6",
                                    "Deep pore cleansing , Relaxing , Vibrant, Invigorating, Cleansing, Prevents Breakouts, Hydrating , P...\n6",
                                    "Maintains the health of the skin. Deep pore Cleansing. Removes impurities. Corrects certain skin con...\n6",
                                    "Removes dirt and debris, followed by a conditioning. Reduces Scalp irritation, Itching and seborrhei...\n6",
                                    "Deposit required. A client consultation must be booked first. *Neck Therapy Relieves follicular infl...\n6",
                                    "*Neck and Chin Treatment* Therapeutic ozone steamer. Removes and reduces the inflammation of bumps a...\n6",
                                    "50%% Deposit required."
                                ],
                                "address": "4320 Deerwood Lake Parkway Unit 104 \nJacksonville, FL 32216",
                                "google_link_address": "https://maps.google.com/maps?q=4320%%20Deerwood%%20Lake%%20Parkway%%2C%%20Unit%%20104%%2C%%20Jacksonville%%2C%%20FL%%2C%%2032216",
                                "phone_number": "9045456414",
                                "business_hours_sunday": "Closed",
                                "business_hours_monday": " 10:00 AM\n-\n 6:00 PM",
                                "business_hours_tuesday": " 10:00 AM\n-\n 7:00 PM",
                                "business_hours_wednesday": " 10:00 AM\n-\n 7:00 PM",
                                "business_hours_thursday": " 10:00 AM\n-\n 7:15 PM",
                                "business_hours_friday": " 9:00 AM\n-\n 7:15 PM",
                                "business_hours_saturday": " 9:00 AM\n-\n 4:30 PM",
                                "cancellation_policy": "You will not be charged if you cancel at least 24 hours before your appointment starts. Otherwise, you will be charged 50%% of service price for late cancellations and 100%% for no shows.",
                                "reviews": "5.0 (535 Reviews)\n1\n<1%%\n2\n<1%%\n3\n<1%%\n4\n3%%\n5\n96%%",
                                "clientPhotosNo": "Get $50",

                                "reviewerNameAndDate": [
                                    "JEFF T.\nFeb 25, 2023",
                                    "QUEEN B.\nAug 17, 2023",
                                    "TRACY H.\nJul 7, 2023",
                                    "STEPHANIE M.\nJun 16, 2023",
                                    "JUSTIN O.\nJun 14, 2023",
                                    "JUSTIN V.\nMay 22, 2023",
                                    "ADRIA P.\nMay 21, 2023",
                                    "LAURIE J.\nMay 9, 2023",
                                    "EDDY ANTONIO B.\nApr 22, 2023",
                                    "JUSTIN V.\nApr 15, 2023",
                                    "MICHELLA B.\nApr 14, 2023",
                                    "JAMAL S.\nApr 8, 2023",
                                    "LOVE PHILLIPS I.\nApr 1, 2023",
                                    "JUSTIN V.\nMar 25, 2023",
                                    "JAMAL S.\nMar 3, 2023",
                                    "NADIA F.\nFeb 25, 2023",
                                    "JEFF T.\nFeb 25, 2023",
                                    "JUSTIN V.\nFeb 18, 2023",
                                    "J C.\nFeb 1, 2023",
                                    "ED P.\nJan 26, 2023",
                                    "EDDY ANTONIO B.\nJan 25, 2023"
                                ],
                                "reviewServiceName": [
                                    "Beard Line-up | Sculpting",
                                    "Women's Under Cut | Neck Trim",
                                    "Men’s Haircut only(Shave not included)",
                                    "Kids/Young Men’s Haircut",
                                    "Men’s Haircut only(Shave not included)",
                                    "Clipper Line-up and/or Shave",
                                    "Kids/Young Men’s Haircut",
                                    "Men's Haircut and Shave",
                                    "Men’s Haircut only(Shave not included)",
                                    "Clipper Line-up and/or Shave",
                                    "Women's Under Cut | Neck Trim",
                                    "Men’s Grooming Package, Eyebrow Arching | Shaping",
                                    "Men's Haircut and Shave",
                                    "Beard Line-up | Sculpting",
                                    "Men's Full Service(Ages: 18 and up)",
                                    "Women's Specialty Haircut",
                                    "Beard Line-up | Sculpting",
                                    "Beard Line-up | Sculpting",
                                    "Basic Men’s Haircut | No Shave (Ages: 18 and up)",
                                    "HydroTherapy “Bald Head” Treatment, Beard Color w/ Beard Line-up| Sculpting",
                                    "Young Men’s Haircut (Ages: 13 to 17)"
                                ],
                                "aboutClientAdjectives": [
                                    [
                                    "ATTENTIVE\nON TIME\nPROFESSIONAL",
                                    "ATTENTIVE\nMETICULOUS\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH",
                                    "LISTENS\nON TIME\nPROFESSIONAL\nTRENDY",
                                    "ATTENTIVE\nLISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL",
                                    "LISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH\nTRENDY",
                                    "ATTENTIVE\nON TIME\nPERSONABLE\nPROFESSIONAL\nTHOROUGH",
                                    "ATTENTIVE\nCREATIVE\nMETICULOUS\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH",
                                    "LISTENS\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE",
                                    "CREATIVE\nLISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL\nTRENDY",
                                    "CREATIVE\nLISTENS\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTRENDY",
                                    "ATTENTIVE\nCREATIVE\nLISTENS\nPROFESSIONAL\nRESPONSIVE",
                                    "ATTENTIVE\nCREATIVE\nLISTENS\nMETICULOUS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH\nTRENDY",
                                    "CREATIVE\nLISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH\nTRENDY",
                                    "ATTENTIVE\nCREATIVE\nLISTENS\nPROFESSIONAL\nRESPONSIVE",
                                    "LISTENS\nPROFESSIONAL\nTHOROUGH",
                                    "ATTENTIVE\nLISTENS\nMETICULOUS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH",
                                    "CREATIVE\nLISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH\nTRENDY",
                                    "ATTENTIVE\nLISTENS\nPERSONABLE\nPROFESSIONAL\nTHOROUGH",
                                    "CREATIVE\nLISTENS\nON TIME\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE\nTHOROUGH\nTRENDY",
                                    "CREATIVE\nLISTENS\nPERSONABLE\nPROFESSIONAL\nRESPONSIVE"
                                    ]
                                ],
                                "aboutName": [
                                    "Hi there, ",
                                    "Im Paul"
                                ],

                                }``` Also don't present booksy at this stage at all, it is only about praising them. Don't let them know that we are booking
                                service provider, check out this examples to help you better frame the compliment:
                                example: Hey [get name from the data within the triple backticks],
                                🌟 I just checked out your profile on [get name from the data within the triple backticks], and I'm seriously impressed with the amazing
                                services you offer at [get business name from the data within the triple backticks]. Your  [Include some of the adjectives or their synonyms
                                [get adjectives from the aboutClientAdjectives within the data in the triple backticks above ] and use them in the conversation.
                                Those are opinions from their clients and they are what distinguish the best professionals. Conclude by wishing them best of luck.
                                Remember the tone of voice above that we mentioned. Don't repeat yourself when using adjectives.] really shine through. 💈✂️.Do not sign off.
                            """
                            try:
                                random_compliment_state = query_gpt(first_compliment_prompt)
                                random_compliment = (
                                    random_compliment_state.get("choices")[0].get("message").get("content")
                                )
                                send_message.delay(random_compliment, username=account.igname)
                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                            }
                            accounts_complimented.append(ready_accounts)

                        elif serializer.data.get("reaction") == 3:

                            try:
                                media_id = cl.media_id(media_pk=user_medias[0].pk)
                                cl.media_like(media_id)
                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "like": True,
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                                "success": True,
                            }
                            accounts_complimented.append(ready_accounts)

                i += 1

        return Response({"accounts": accounts_complimented})
