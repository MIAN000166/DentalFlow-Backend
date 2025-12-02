import requests
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SERankingKeyword
from seo.serialzer import SERankingKeywordSerializer
from core.permission import UserAuthenticated

#API_KEY = "0f17186d-81be-10bc-8f4f-655f54e09857"
API_KEY = "6e21a93c-33d8-c9ce-9607-55e03143af8d"
DEFAULT_DOMAIN = "seranking.com"
API_URL_TEMPLATE = "https://api.seranking.com/v1/domain/keywords?source=us&domain={domain}&type=organic"

class SERankingKeywordViewSet(ModelViewSet):

    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def fetch_keywords(self, request):
        user = request.user
        domain = request.data.get("domain", "seranking.com")
        source = request.data.get("source", "us")  
        type_ = request.data.get("type", "organic")

        if not domain:
            return Response(
                {"status": False, "message": "domain is required"},
                status=400
            )

        url = f"https://api.seranking.com/v1/domain/keywords?source={source}&domain={domain}&type={type_}"
        print(url)
        headers = {
            "Authorization": f"Token {API_KEY}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from SERanking API. Status: {response.status_code}"
            }, status=400)

        data = response.json()

        created_records = []
        total_volume = 0
        total_traffic = 0
        total_price = 0

        # Save all keyword entries
        for item in data:
            obj = SERankingKeyword.objects.create(
                user=request.user,
                domain=domain,
                keyword=item.get("keyword"),
                block_type=item.get("block_type"),
                block_position=item.get("block_position"),
                position=item.get("position"),
                prev_pos=item.get("prev_pos"),
                volume=item.get("volume"),
                cpc=item.get("cpc"),
                competition=item.get("competition"),
                url=item.get("url"),
                difficulty=item.get("difficulty"),
                total_sites=item.get("total_sites"),
                traffic=item.get("traffic"),
                traffic_percent=item.get("traffic_percent"),
                price=item.get("price"),
            )
            created_records.append(SERankingKeywordSerializer(obj).data)
            
            # Add to totals
            total_volume += item.get("volume", 0)
            total_traffic += item.get("traffic", 0)
            total_price += item.get("price", 0)

        return Response({
            "status": True,
            "message": "Data saved successfully",
            "total_count": len(data),  # Total number of records
            "total_volume": total_volume,  # Total volume sum
            "total_traffic": total_traffic,  # Total traffic sum
            "total_price": total_price,  # Total price sum
            "records": created_records
        })
