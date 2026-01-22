from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User as FBUser
from facebook_business.adobjects.adset import AdSet
import requests
import base64
import os
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adpreview import AdPreview
from datetime import datetime, timedelta
from django.contrib.auth.models import User  # Just to satisfy ModelViewSet queryset
import requests
from .models import FacebookProfile
from .serializers import FacebookConnectSerializer, PostContentSerializer

class FacebookManagerViewSet(viewsets.ModelViewSet):
    """
    Ek hi ViewSet mein saari Facebook functionality handle hogi using @action.
    """
    queryset = User.objects.none()  # Abhi hum DB use nahi kr rhy, isliye empty queryset
    serializer_class = None         # Abhi serializer ki zaroorat nahi
    APP_ID = '852721637524289'
    APP_SECRET = '153b212ec134da245cfcc7e82510614e'
    # Ye URL same honi chahiye jo Meta Console mein "Valid OAuth Redirect URIs" mein hai
    REDIRECT_URI = 'http://localhost:8000/api/fb-manager/callback/'
    def get_fb_credentials(self, request):
        """Helper function to get App ID/Secret & Token"""
        return {
            'app_id': '852721637524289',
            'app_secret': '153b212ec134da245cfcc7e82510614e',
            'access_token': request.data.get('access_token')
        }
    
    @action(detail=False, methods=['get'])
    def get_login_url(self, request):
        """
        Frontend is API ko call karega taa k pata chale user ko kahan redirect karna hai.
        """
        # scope = 'email,pages_show_list,ads_management,ads_read,pages_read_engagement,business_management'
        # 'email' hata diya hai, ab ye error nahi dega
        scope = 'pages_show_list,ads_management,ads_read,pages_read_engagement,business_management'
        
        url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.APP_ID}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"scope={scope}&"
            f"response_type=code"
        )
        return Response({"auth_url": url})
    
    # --- API 2: CODE SE TOKEN BANANA AUR SAVE KARNA ---
    @action(detail=False, methods=['post'])
    def handle_callback(self, request):
        """
        User login k baad 'code' le kar wapis ayega. Hum us code se token banayen gy
        aur Database mein save kar len gy.
        """
        code = request.data.get('code')
        if not code:
            return Response({"error": "Code is missing"}, status=400)

        # 1. Exchange Code for Access Token
        token_url = (
            f"https://graph.facebook.com/v18.0/oauth/access_token?"
            f"client_id={self.APP_ID}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"client_secret={self.APP_SECRET}&"
            f"code={code}"
        )
        
        try:
            resp = requests.get(token_url).json()
            if 'access_token' not in resp:
                return Response({"error": "Failed to get token", "details": resp}, status=400)
            
            access_token = resp['access_token']

            # 2. Database mein Save karein
            user = request.user
            if user.is_anonymous: user = User.objects.first() # Testing hack

            # Save token to DB
            FacebookProfile.objects.update_or_create(
                user=user,
                defaults={'access_token': access_token}
            )

            return Response({"message": "Login Successful! Token Saved.", "status": "connected"})

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # --- ACTION 1: Full Connection Test ---
    @action(detail=False, methods=['post'])
  
    def test_connection(self, request):
        # 1. Credentials
        app_id = '852721637524289'
        app_secret = '153b212ec134da245cfcc7e82510614e'
        token = request.data.get('access_token') or request.data.get('token')

        if not token:
            return Response({"error": "Access Token is required"}, status=400)

        FacebookAdsApi.init(app_id, app_secret, token)
        
        data = {
            "status": "checked",
            "pages": [],
            "ad_accounts": [],
            "debug_info": []
        }

        # --- STEP 1: General List Fetch (Jo pehle kar rahy thay) ---
        try:
            url = "https://graph.facebook.com/v18.0/me/accounts"
            params = {'access_token': token, 'fields': 'name,id,category,access_token,tasks'}
            resp = requests.get(url, params=params).json()
            
            if 'data' in resp:
                data['pages'].extend(resp['data'])
            else:
                data['debug_info'].append(f"List Fetch Empty: {resp}")

        except Exception as e:
            data['debug_info'].append(f"List Error: {str(e)}")

        # --- STEP 2: DIRECT TARGET FETCH (The Fix 🛠️) ---
        # Agar list khali hai, to hum seedha 'mo_elias_d' ki ID ko hit karein gy
        target_page_id = '112591256879208'
        
        # Check karein k kya ye page already list mein aa gaya? Agar nahi to fetch karein
        already_found = any(p['id'] == target_page_id for p in data['pages'])
        
        if not already_found:
            try:
                # Direct Page Call
                direct_url = f"https://graph.facebook.com/v18.0/{target_page_id}"
                direct_params = {'access_token': token, 'fields': 'name,id,access_token,category'}
                direct_resp = requests.get(direct_url, params=direct_params).json()
                
                if 'id' in direct_resp:
                    data['pages'].append({
                        "name": direct_resp.get('name'),
                        "id": direct_resp.get('id'),
                        "category": direct_resp.get('category'),
                        "source": "Direct Fetch (Granular Access)"
                    })
                    data['debug_info'].append("Success! Found page via Direct ID fetch.")
                else:
                    data['debug_info'].append(f"Direct Fetch Failed: {direct_resp}")
            except Exception as e:
                data['debug_info'].append(f"Direct Fetch Error: {str(e)}")

        # --- STEP 3: Ad Accounts ---
        try:
            me = FBUser(fbid='me')
            my_accounts = me.get_ad_accounts(fields=['name', 'account_id', 'currency'])
            for acc in my_accounts:
                data['ad_accounts'].append(acc.export_all_data())
        except Exception as e:
            data['debug_info'].append(f"Ad Account Error: {str(e)}")

        return Response(data)
    # --- ACTION 2: Get Only Pages ---
    @action(detail=False, methods=['get'])
    def get_my_pages(self, request):
        """
        Ye API Database se token uthayegi aur Facebook se Pages la kar degi.
        Frontend isy 'Dashboard' par dikhaye ga.
        """
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            # Database se Token nikalo
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected. Please login first."}, status=401)

        # Facebook se Pages mangwana
        try:
            # Pehle '/me/accounts' try karein
            url = "https://graph.facebook.com/v18.0/me/accounts"
            params = {'access_token': token, 'fields': 'name,id,category,tasks'}
            response = requests.get(url, params=params).json()
            
            pages_list = response.get('data', [])

            # Agar list khali hai (Granular access issue), to 'mo_elias_d' ko direct fetch karein
            if not pages_list:
                target_id = '112591256879208' # Client Page ID
                direct_url = f"https://graph.facebook.com/v18.0/{target_id}"
                direct_resp = requests.get(direct_url, params={'access_token': token, 'fields': 'name,id,category'}).json()
                if 'id' in direct_resp:
                    pages_list.append(direct_resp)

            return Response({"pages": pages_list})

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # --- ACTION 3: Get Only Ad Accounts ---
    @action(detail=False, methods=['post'])
    def get_ad_accounts(self, request):
      
        app_id = '852721637524289'
        app_secret = '153b212ec134da245cfcc7e82510614e'

        # --- CHANGE 1: Token Database se lena ---
        user = request.user
        if user.is_anonymous: user = User.objects.first() # Testing hack

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected. Please login with Facebook first."}, status=400)
        
        # ----------------------------------------

        try:
            FacebookAdsApi.init(app_id, app_secret, token)
            me = FBUser(fbid='me')
            
            # Ad Accounts fetch karna
            accounts = me.get_ad_accounts(fields=['name', 'account_id', 'account_status', 'amount_spent', 'currency'])
            
            clean_data = [acc.export_all_data() for acc in accounts]
            return Response({"ad_accounts": clean_data})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def create_campaign(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        ad_account_id = request.data.get('ad_account_id')
        campaign_name = request.data.get('name', 'New Campaign via API')
        objective = request.data.get('objective', 'OUTCOME_TRAFFIC')
        status = request.data.get('status', 'PAUSED')
        special_ad_categories = request.data.get('special_ad_categories', [])

        if not ad_account_id:
            return Response({"error": "Ad Account ID is required"}, status=400)

        try:
            account = AdAccount(ad_account_id)

            params = {
                'name': campaign_name,
                'objective': objective,
                'status': status,
                'special_ad_categories': special_ad_categories or ['NONE'],
                'buying_type': 'AUCTION',
                'is_adset_budget_sharing_enabled': False 
            }

            campaign = account.create_campaign(params=params)

            # --- ERROR FIX HUA YAHAN ---
            # Hum 'campaign['name']' ki bajaye variable 'campaign_name' use kar rahy hain
            return Response({
                "message": "Campaign Created Successfully!",
                "campaign_id": campaign['id'], 
                "campaign_name": campaign_name, # Fixed Line
                "objective": objective
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

   
    @action(detail=False, methods=['post'])
    def create_ad_set(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        # 1. Inputs
        ad_account_id = request.data.get('ad_account_id')
        campaign_id = request.data.get('campaign_id')
        name = request.data.get('name', 'New Ad Set')
        daily_budget = request.data.get('daily_budget', '100000')
        
        geo_location = request.data.get('geo_locations', {"countries": ["PK"]})
        age_min = request.data.get('age_min', 18)
        age_max = request.data.get('age_max', 65)

        if not ad_account_id or not campaign_id:
            return Response({"error": "Ad Account ID and Campaign ID are required"}, status=400)

        try:
            account = AdAccount(ad_account_id)
            
            # Start Time: 10 min from now
            start_time = datetime.now() + timedelta(minutes=10)
            
            params = {
                'name': name,
                'campaign_id': campaign_id,
                'daily_budget': daily_budget,
                'billing_event': 'IMPRESSIONS',
                'optimization_goal': 'LINK_CLICKS',
                'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
                'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'status': 'PAUSED',
                'targeting': {
                    'geo_locations': geo_location,
                    'age_min': age_min,
                    'age_max': age_max,
                    'publisher_platforms': ['facebook', 'instagram'],
                    'device_platforms': ['mobile', 'desktop'],
                    
                    # --- FIX: Advantage+ Audience Flag ---
                    'targeting_automation': {
                        'advantage_audience': 0  # 0 = Manual Control (Strict), 1 = AI Auto
                    }
                }
            }

            adset = account.create_ad_set(params=params)

            return Response({
                "message": "Ad Set Created Successfully!",
                "adset_id": adset['id'],
                "adset_name": name,
                "campaign_id": campaign_id
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def create_ad_creative(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        # 1. Inputs
        ad_account_id = request.data.get('ad_account_id')
        page_id = request.data.get('page_id')
        image_url = request.data.get('image_url')
        headline = request.data.get('headline', 'Chat with us!')
        primary_text = request.data.get('primary_text', 'Best Dental Services in Town.')
        link_url = request.data.get('link_url', 'https://www.example.com')
        
        if not ad_account_id or not page_id or not image_url:
            return Response({"error": "Ad Account ID, Page ID and Image URL are required"}, status=400)

        try:
            account = AdAccount(ad_account_id)

            # --- A. Image Download (Memory) ---
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, headers=headers)
            if response.status_code != 200:
                return Response({"error": "Failed to download image."}, status=400)
            
            image_bytes = base64.b64encode(response.content).decode('utf-8')
            image_filename = 'ad_image.jpg'

            # --- B. Upload to Facebook ---
            image_response = account.create_ad_image(params={
                'name': image_filename,
                'bytes': image_bytes, 
            })
            
            # --- C. Hash Extraction (SIMPLIFIED FIX) ---
            # Error log ne bataya k 'hash' top level par hi mojood hai.
            # Hum pehle direct check karenge, phir list fallback rakhenge.
            
            image_hash = None
            
            # 1. Direct Access (Jo apke error log mein tha)
            if hasattr(image_response, 'get'):
                image_hash = image_response.get('hash')
            
            # 2. Agar List ho (Fallback)
            if not image_hash and isinstance(image_response, list) and len(image_response) > 0:
                 image_hash = image_response[0].get('hash')

            if not image_hash:
                 # Debugging k liye wapis pura response bhej denge agar fail hua
                 return Response({"error": f"Hash not found. Response: {str(image_response)}"}, status=400)

            # --- D. Creative Create ---
            creative_params = {
                'name': 'Creative - ' + headline,
                'object_story_spec': {
                    'page_id': page_id,
                    'link_data': {
                        'image_hash': image_hash,
                        'link': link_url,
                        'message': primary_text,
                        'name': headline,
                        'call_to_action': {
                            'type': 'LEARN_MORE',
                            'value': {'link': link_url}
                        }
                    }
                }
            }
            
            creative = account.create_ad_creative(params=creative_params)

            return Response({
                "message": "Creative Created Successfully!",
                "creative_id": creative['id'],
                "image_hash": image_hash
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)