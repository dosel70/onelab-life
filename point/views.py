from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Sum
from django.http import JsonResponse,HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views import View

from rest_framework.utils import json
from rest_framework.views import APIView
import math

from member.models import Member
from place.models import  Place
from placeMember.models import PlaceMember
from point.models import Point
from school.models import School
from share.models import Share
from shareMember.models import ShareMember
from university.models import University


class PointView(View):
    def get(self, request):
        # 세션에 저장된 멤버를 가져옴
        member = request.session['member']
        # context에 멤버를 담아서 화면에 전달
        context = {
            'member': member
        }
        return render(request, 'point/point-charge.html', context)

    def post(self, request):
        # fetch의 json 형태의 body 정보를 문자열로 디코딩함 (utf-8)
        data = json.loads(request.body.decode('utf-8'))
        # fetch 내의 data에서 point를 가져옴 --> 실제 결제 금액
        point = data.get('point')
        # 세션에 저장된 멤버의 id를 가져옴
        member_id = request.session['member']['id']
        datas = {
            'point': point, # 포인트
            'member_id': member_id, # 멤버 아이디
            'point_status': 1  # 충전 상태
        }
        # University 모델에서 member_id가 member_id인것을 조회하고 그중 첫번째 객체를 가져옴
        university = University.objects.filter(member_id=member_id).first()
        # 대학생 회원일때
        if university:
            # Point 모델에 datas 변수값을 생성함
            point_obj = Point.objects.create(**datas)
            print(f'충전된 금액 -> {point}point')

            # 대학생 포인트에 추가
            university.university_member_points += point_obj.point
            # 대학생 수정 정보 저장
            university.save()
            # 결과값 리턴
            return JsonResponse({'success': True, 'message': '성공!!'})
        # 대학생 회원이 아닐때
        else:
            # 오류 결과값 리턴
            return JsonResponse({'success': False, 'message': '대학생만 충전이 가능합니다'})


# 포인트 충전 내역 View----------------------------------
class PointListView(View):
    def get(self, request):
        member_id = request.session['member']['id']

        # 페이지 번호 가져오기
        page = request.GET.get('page', 1)

        # 포인트 리스트 가져오기
        point_list = Point.objects.filter(member_id=member_id, point_status=1).order_by('-id')

        # Paginator를 사용하여 페이지당 원하는 개수로 나누기
        paginator = Paginator(point_list, 8)  # 8개씩 보여주기로 설정 (원하는 개수로 변경 가능)

        # 포인트가 있을때,
        try:
            points = paginator.page(page)
        except EmptyPage:
            points = paginator.page(paginator.num_pages)

        context = {
            'member': request.session['member'],
            'member_id': member_id,
            'points': points,
        }

        return render(request, 'point/pay-list.html', context)


class PointListAPI(APIView):
    def get(self, request):
        page = request.GET.get('page', 1)
        type = request.GET.get('type', '')
        keyword = request.GET.get('keyword', '')
        order = request.GET.get('order', 'recent')
        page = int(request.GET.get('page', 1))

        condition = Q()
        if type:
            for t in list(type):
                if t == 't':
                    condition |= Q(post_title__contains=keyword)

                elif t == 'c':
                    condition |= Q(post_content__contains=keyword)

                elif t == 'w':
                    condition |= Q(member__member_name__contains=keyword)

        row_count = 5
        offset = (page - 1) * row_count
        limit = page * row_count
        total = Point.enabled_objects.filter(condition).count()
        page_count = 5

        end_page = math.ceil(page / page_count) * page_count
        start_page = end_page - page_count + 1
        real_end = math.ceil(total / row_count)
        end_page = real_end if end_page > real_end else end_page

        if end_page == 0:
            end_page = 1

        context = {
            'total': total,
            'order': order,
            'start_page': start_page,
            'end_page': end_page,
            'page': page,
            'real_end': real_end,
            'page_count': page_count,
            'type': type,
            'keyword': keyword,
        }
        ordering = '-id'
        if order == 'popular':
            ordering = '-id'

        context['points'] = list(Point.enabled_objects.filter(condition).order_by(ordering))[offset:limit]

        return render(request, 'point/pay-list.html', context)


class PointListDetailView(View):
    def get(self, request):
        member = request.session['member']
        member_id = request.session['member']['id']

        point_id = request.GET.get('id')
        point = Point.objects.get(id=point_id, member_id=member_id)

        context = {
            'date': Point.objects.filter(member_id=member_id).values('updated_date').first(),
            'member': member,
            'member_id': member_id,
            'point': point,
        }
        return render(request, 'point/pay-list-detail.html', context)

# ------------------------------------------------------------------------------
    # 포인트 사용 View
class PointUseListView(View):
    def get(self, request):
        member_id = request.session['member']['id']

        # 페이지 번호 가져오기
        page = request.GET.get('page', 1)

        # 포인트 리스트 가져오기
        point_list = Point.objects.filter(member_id=member_id, point_status=2).order_by('-id')

        # Paginator를 사용하여 페이지당 원하는 개수로 나누기
        paginator = Paginator(point_list, 8)  # 8개씩 보여주기로 설정 (원하는 개수로 변경 가능)

        try:
            points = paginator.page(page) # 페이지 목록을 불러온다.
        except EmptyPage: # 불러올 페이지가 없는경우
            points = paginator.page(paginator.num_pages) # 페이지가 비어 있는 경우 마지막 페이지로 이동한다.

        context = {
            'member': request.session['member'], # 현재 로그인한 회원의 정보
            'member_id': member_id, # 멤버 아이디
            'points': points, # 포인트 리스트
        }

        return render(request, 'point/use-list.html', context)

# 포인트 사용 상세 내역 View
class PointUseDetailView(View):

    def get(self, request):
        # 세션에서 현재 로그인한 회원 정보를 가져온다
        member = request.session['member']
        member_id = request.session['member']['id']  # 현재 로그인한 회원의 ID를 가져온다.
        point_id = request.GET.get('id')  # GET 요청에서 포인트 ID를 가져온다.

        try:
            point = Point.objects.get(id=point_id, member_id=member_id)  # 해당 ID의 포인트를 가져온다.
        except Point.DoesNotExist:
            # 포인트가 존재하지 않는 경우 처리
            return HttpResponseNotFound("Point does not exist")

        # 현재 회원이 속한 PlaceMember 모델을 가져온다.
        place_true = PlaceMember.objects.filter(university=member_id).first()
        print(place_true)
        # 현재 회원이 속한 대학의 ShareMember 모델을 가져온다.
        share_true = ShareMember.objects.filter(university=member_id).first()
        print(share_true)

        context = {
            'date': point.updated_date,  # 포인트 업데이트 날짜를 컨텍스트에 추가
            'member': member,  # 회원 정보를 컨텍스트에 추가.
            'member_id': member_id,  # 회원 ID를 컨텍스트에 추가
            'point': point,  # 포인트 정보를 컨텍스트에 추가
        }

        if place_true:
            # PlaceMember에 현재 회원이 존재하는 경우, 해당 장소 정보를 가져온다.
            place = Place.objects.get(id=place_true.place_id)
            context['place'] = place
            context['place_true'] = place_true
            context['place_title'] = place.place_title
            context['place_points'] = place.place_points

        if share_true:
            # ShareMember에 현재 회원이 존재하는 경우, 해당 자료 공유 정보를 가져온다.
            share = Share.objects.get(id=share_true.share_id)
            # 자료 공유내에 있는 대학생 정보를 불러옴
            share_name = University.objects.get(member_id=share.university)
            # 자료 공유 내에 있는 대학생 모델을 통해  Member 모델에서 조회
            sale_member = Member.objects.get(id=share_name.member_id)
            print(sale_member)
            context['share'] = share # 자료공유정보
            context['sale_member'] = sale_member # 자료공유 판매자
            context['share_true'] = share_true # 자료 공유 구매자
            context['share_title'] = share.share_title # 자료 공유 제목
            context['share_points'] = share.share_points # 자료 공유 가격

        # 포인트 사용 내역 상세 페이지를 렌더링하여 반환.
        return render(request, 'point/use-list-detail.html', context)



#------------적립 내역 view-------------------------
class PointGetListView(View):
    def get(self, request):
        member_id = request.session['member']['id']  # 세션에 저장된 멤버의 아이디를 불러온다.

        # 페이지 번호 가져오기
        page = request.GET.get('page', 1)

        # 포인트 리스트 가져오기
        point_list = Point.objects.filter(member_id=member_id, point_status=3).order_by('-id')

        # Paginator를 사용하여 페이지당 원하는 개수로 나누기
        paginator = Paginator(point_list, 8)  # 8개씩 보여주기로 설정 (원하는 개수로 변경 가능)

        try:
            points = paginator.page(page)  # 해당 페이지의 포인트 리스트를 가져온다.
        except EmptyPage:
            # 페이지가 비어있는 경우, 마지막 페이지로 이동
            points = paginator.page(paginator.num_pages)

        # 컨텍스트 설정
        context = {
            'member': request.session['member'],  # 현재 로그인한 회원 정보
            'member_id': member_id,  # 현재 로그인한 회원의 아이디
            'points': points,  # 해당 페이지의 포인트 리스트
        }

        return render(request, 'point/get-list.html', context)  # 포인트 리스트를 보여주는 HTML 페이지를 렌더링


class PointGetDetailView(View):
    def get(self, request):
        # 현재 세션에 저장된 멤버
        member = request.session['member']
        # 멤버의 아이디를 불러온다.
        member_id = request.session['member']['id']
        # GET 방식으로 요청해서 id를 불러온다.
        point_id = request.GET.get('id')
        # Point 모델에서 point 아이디와 member_id를 조회해서 불러온다.
        point = Point.objects.get(id=point_id, member_id=member_id)

        # Place 모델에서 school_id와 member_id를 서로 조회해서 그중 첫번째 객체를 가져온다.
        place_true = Place.objects.filter(school=member_id).first()
        # Share 모델에서 university_id와 member_id를 서로 조회햇 그중 첫번째 객체를 가져온다.
        share_true = Share.objects.filter(university=member_id).first()

        context = {
            'date': Point.objects.filter(member_id=member_id).values('updated_date').first(), # 포인트 업데이트 날짜
            'member': member, # 멤버 정보
            'member_id': member_id, # 멤버 아이디
            'point': point, # 포인트 리스트
            'school': School.objects.filter(member_id=member_id).values('school_name').first() # 학교 이름
        }

        # 장소를 공유한 적이 있는 회원일때 즉 장소 공유 데이터가 존재할때,
        if place_true :
            # Place에서 school아이디와 member아이디를 서로 조회해서 그중 첫번째 객체를 가져온다.
            place_id = Place.objects.filter(school=member_id).first()
            # Point에서 실제 아이디를 조회해서 불러온다.
            place_point = Point.objects.get(id=point_id)
            # 장소공유 제목을 가져온다.
            place_title = place_true.place_title
            # 장소공유 포인트를 가져온다.
            place_points = place_true.place_points

            context['place'] = place_id # 장소공유 중 첫번째 객체의 정보
            context['place_true'] = place_true # 장소 공유 정보
            context['place_point'] = place_point # 포인트 정보
            context['place_points'] = place_points # 장소 공유 포인트
            context['place_title'] = place_title # 장소 공유 제목

        # 자료 공유를 한 적 이 있는 회원일 때 즉 자료 공유 데이터가 존재할 때,
        if share_true :
            # 자료 공유에서 university_id와 member_id를 서로 조회해서 첫번째 객체를 가져온다.
            share_id = Share.objects.filter(university=member_id).first()
            # Point에서 실제 아이디를 조회해서 불러온다.
            share_point = Point.objects.get(id=point_id)
            # 자료 공유 제목을 불러온다.
            share_title = share_true.share_title
            # 자료 공유 가격을 불러온다.
            share_points = share_true.share_points


            context['share'] = share_id # 자료 공유 중 첫번째 객체의 정보
            context['share_true'] = share_true # 자료 공유 정보
            context['share_points'] = share_point # 포인트 정보
            context['share_points'] = share_points # 자료 공유 포인트 정보
            context['share_title'] = share_title # 자료 공유 제목

        # 적립내역 상세보기인 get-list-detail.html 에 렌더링한다.
        return render(request, 'point/get-list-detail.html', context)
