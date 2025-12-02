import requests
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permission import UserAuthenticated
from rest_framework import status
from seo.models import(
    SERankingKeyword,
    Competitor,
    SimilarKeyword,
    RelatedKeyword,
    DomainHistory,
    AuditReport
)
from seo.serialzer import(
    SERankingKeywordSerializer,
    CompetittorSerializer,
    SimilarKeywordSerializer,
    RelatedKeywordSerializer,
    DomainHistorySerializer,
    AuditReportSerializer
)

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
            "total_count": len(data), 
            "total_volume": total_volume,
            "total_traffic": total_traffic, 
            "total_price": total_price,
            "records": created_records
        })

    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def fetch_competitors(self, request):
        user = request.user
        domain = request.data.get("domain")
        source = request.data.get("source")
        type_ = request.data.get("type")

        if not domain:
            return Response(
                {"status": False, "message": "domain is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = f"https://api.seranking.com/v1/domain/competitors?domain={domain}&type={type_}&source={source}"
        headers = {
            "Authorization": f"Token {API_KEY}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from SERanking API. Status: {response.status_code}"
            }, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        created_records = []
        total_common_keywords = 0

        for item in data:
            competitor, created = Competitor.objects.update_or_create(
                user=user,
                domain=item.get("domain"),
                defaults={'common_keywords': item.get("common_keywords")}
            )
            created_records.append(CompetittorSerializer(competitor).data)

            total_common_keywords += item.get("common_keywords", 0)

        return Response({
            "status": True,
            "message": "Competitors data saved successfully",
            "total_count": len(data),
            "total_common_keywords": total_common_keywords,
            "records": created_records
        })
    
    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def fetch_similar_keywords(self, request):
        user = request.user
        keyword = request.data.get("keyword")
        source = request.data.get("source")
        limit = request.data.get("limit", 100)

        if not keyword:
            return Response(
                {"status": False, "message": "keyword is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = (
            f"https://api.seranking.com/v1/keywords/similar?"
            f"source={source}&keyword={keyword}&limit={limit}&offset=0&sort=keyword&sort_order=asc"
            f"&history_trend=true&filter[volume][from]=100&filter[volume][to]=100000"
            f"&filter[difficulty][from]=0&filter[difficulty][to]=30&filter[cpc][from]=0&filter[cpc][to]=100"
            f"&filter[competition][from]=0&filter[competition][to]=0.1"
            f"&filter[keyword_count][from]=3&filter[keyword_count][to]=8"
            f"&filter[characters_count][from]=15&filter[characters_count][to]=50"
            f"&filter[serp_features]=sge,images"
        )

        headers = {"Authorization": f"Token {API_KEY}"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from SERanking API. Status: {response.status_code}"
            }, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        keywords = data.get("keywords", [])

        total_volume = 0
        total_difficulty = 0
        total_cpc = 0
        total_competition = 0
        created_records = []

        for item in keywords:
            obj, created = SimilarKeyword.objects.update_or_create(
                user=user,
                keyword=item.get("keyword"),
                defaults={
                    "cpc": item.get("cpc", 0),
                    "difficulty": item.get("difficulty", 0),
                    "volume": item.get("volume", 0),
                    "competition": item.get("competition", 0),
                    "serp_features": item.get("serp_features", []),
                    "intents": item.get("intents", []),
                    "history_trend": item.get("history_trend", {}),
                }
            )
            created_records.append(SimilarKeywordSerializer(obj).data)

            total_volume += item.get("volume", 0)
            total_difficulty += item.get("difficulty", 0)
            total_cpc += item.get("cpc", 0)
            total_competition += item.get("competition", 0)

        return Response({
            "status": True,
            "message": "Similar keywords data saved successfully",
            "total_count": len(keywords),
            "total_volume": total_volume,
            "total_difficulty": total_difficulty,
            "total_cpc": total_cpc,
            "total_competition": total_competition,
            "records": created_records
        })
    
    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def fetch_related_keywords(self, request):
        user = request.user
        keyword = request.data.get("keyword")
        source = request.data.get("source")
        limit = request.data.get("limit", 10)

        if not keyword:
            return Response(
                {"status": False, "message": "keyword is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = (
            f"https://api.seranking.com/v1/keywords/related?"
            f"source={source}&keyword={keyword}&limit={limit}&offset=0&sort=keyword&sort_order=asc"
            f"&history_trend=true&filter[volume][from]=100&filter[volume][to]=100000"
            f"&filter[difficulty][from]=0&filter[difficulty][to]=30&filter[cpc][from]=0&filter[cpc][to]=100"
            f"&filter[competition][from]=0&filter[competition][to]=0.1"
            f"&filter[keyword_count][from]=3&filter[keyword_count][to]=8"
            f"&filter[characters_count][from]=15&filter[characters_count][to]=50"
            f"&filter[serp_features]=sge,images"
        )

        headers = {"Authorization": f"Token {API_KEY}"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from SERanking API. Status: {response.status_code}"
            }, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        keywords = data.get("keywords", [])

        total_volume = 0
        total_difficulty = 0
        total_cpc = 0
        total_competition = 0
        created_records = []

        for item in keywords:
            obj, created = RelatedKeyword.objects.update_or_create(
                user=user,
                keyword=item.get("keyword"),
                defaults={
                    "cpc": item.get("cpc", 0),
                    "difficulty": item.get("difficulty", 0),
                    "volume": item.get("volume", 0),
                    "competition": item.get("competition", 0),
                    "serp_features": item.get("serp_features", []),
                    "intents": item.get("intents", []),
                    "history_trend": item.get("history_trend", {}),
                }
            )
            created_records.append(RelatedKeywordSerializer(obj).data)

            total_volume += item.get("volume", 0)
            total_difficulty += item.get("difficulty", 0)
            total_cpc += item.get("cpc", 0)
            total_competition += item.get("competition", 0)

        return Response({
            "status": True,
            "message": "Related keywords data saved successfully",
            "total_count": len(keywords),
            "total_volume": total_volume,
            "total_difficulty": total_difficulty,
            "total_cpc": total_cpc,
            "total_competition": total_competition,
            "records": created_records
        })
    
    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def fetch_history(self, request):
        user = request.user
        domain = request.data.get("domain")
        source = request.data.get("source")
        type_ = request.data.get("type")

        if not domain:
            return Response(
                {"status": False, "message": "domain is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = f"https://api.seranking.com/v1/domain/overview/history?source={source}&domain={domain}&type={type_}"
        headers = {"Authorization": f"Token {API_KEY}"}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from SERanking API. Status: {response.status_code}"
            }, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        total_keywords = 0
        total_traffic = 0
        total_price = 0
        created_records = []

        for item in data:
            obj, created = DomainHistory.objects.update_or_create(
                user=user,
                domain=domain,
                year=item.get("year"),
                month=item.get("month"),
                defaults={
                    "keywords_count": item.get("keywords_count", 0),
                    "traffic_sum": item.get("traffic_sum", 0),
                    "top1_2": item.get("top1_2", 0),
                    "top3_5": item.get("top3_5", 0),
                    "top6_8": item.get("top6_8", 0),
                    "top9_11": item.get("top9_11", 0),
                    "price_sum": item.get("price_sum", 0),
                }
            )
            created_records.append(DomainHistorySerializer(obj).data)

            total_keywords += item.get("keywords_count", 0)
            total_traffic += item.get("traffic_sum", 0)
            total_price += item.get("price_sum", 0)

        return Response({
            "status": True,
            "message": "Domain history data saved successfully",
            "total_count": len(data),
            "total_keywords": total_keywords,
            "total_traffic": total_traffic,
            "total_price": total_price,
            "records": created_records
        })
    
    @action(detail=False, methods=["post"], permission_classes=[UserAuthenticated])
    def audit_report(self, request):
        audit_id = request.data.get("audit_id")
        if not audit_id:
            return Response({"status": False, "message": "audit_id is required"}, status=400)

        url = f"https://api.seranking.com/v1/site-audit/audits/report?audit_id={audit_id}&apikey={API_KEY}"
        
        response = requests.get(url)

        if response.status_code != 200:
            return Response({"status": False, "message": f"Failed to fetch data. Status: {response.status_code}"}, status=400)

        data = response.json()

        domain_props = data.get("domain_props", {})
        chromeux = data.get("chromeux", {})

        report = AuditReport.objects.create(
            user=request.user,
            total_pages=data.get("total_pages"),
            total_warnings=data.get("total_warnings"),
            total_errors=data.get("total_errors"),
            total_passed=data.get("total_passed"),
            total_notices=data.get("total_notices"),
            is_finished=data.get("is_finished"),
            dp_dt=domain_props.get("dt"),
            dp_domain=domain_props.get("domain"),
            dp_domains=domain_props.get("domains"),
            dp_expdate=domain_props.get("expdate"),
            dp_updated=domain_props.get("updated"),
            dp_backlinks=domain_props.get("backlinks"),
            dp_all_checked=domain_props.get("all_checked"),
            dp_index_google=domain_props.get("index_google"),
            score_percent=data.get("score_percent"),
            weighted_score_percent=data.get("weighted_score_percent"),
            screenshot=data.get("screenshot"),
            audit_time=data.get("audit_time"),
            version=data.get("version"),
            chromeux_mobile=chromeux.get("mobile"),
            chromeux_desktop=chromeux.get("desktop"),
        )

        return Response(AuditReportSerializer(report).data)
    
    @action(detail=False, methods=["GET"], permission_classes=[UserAuthenticated])
    def fetch_audit_data(self, request):

        url = f"https://api.seranking.com/v1/site-audit/audits?apikey={API_KEY}"
        
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return Response({"status": True, "data": data}, status=200)
        else:
            return Response({
                "status": False,
                "message": f"Failed to fetch data from API. Status: {response.status_code}"
            }, status=400)