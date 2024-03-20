import json
from oneLabProject.settings import MEDIA_URL
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView
from onelab.models import OneLab, OneLabFile
from onelabMember.models import OneLabMember
from place.models import Place, PlaceLike, PlaceFile
from community.models import Community, CommunityFile
from exhibition.models import Exhibition
from highschool.models import HighSchool
from member.models import Member, MemberFile
from member.serializers import MemberSerializer
from placeMember.models import PlaceMember
from point.serializers import PointSerializer
from point.models import Point
from school.models import School
from share.models import Share
from shareMember.models import ShareMember
from university.models import University
from file.models import File
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
#-----import 부분 주석처리 ----------#

# 마이페이지 메인 화면에 들어갈 기능 구현 View
class MyPageMainView(View):
    def get(self, request):
        # 로그인된 회원을 선언한다. => member_id (세션에 저장되있는 member의 id를 불러옴)
        member_id = request.session['member']['id']
        # University model에서 member_id 컬럼이 member_id 변수와 일치하는지 확인하고 그 중 첫번째 객체를 가져옴
        university = University.objects.filter(member_id=member_id).first()
        # Highschool model에서 member_id 컬럼이 member_id 변수와 일치하는지 확인하고 그 중 첫번째 객체를 가져옴
        highschool = HighSchool.objects.filter(member_id=member_id).first()
        # school model에서 member_id 컬럼이 member_id 변수와 일치하는지 확인하고 그 중 첫번째 객체를 가져옴
        school = School.objects.filter(member_id=member_id).first()
        # MemberFile model 에서 member_id가 서로 일치하는지 확인하고 첫번째 객체를 가져옴
        profile = MemberFile.objects.filter(member_id=member_id).first()


        # 공모전 목록 가져오기

        # 대학생인 경우에만 적용 (공모전 참여자는 대학생회원만 가능)
        if university:
            # 공모전 목록에서 기존 ExhibitionMember의 university_id를 역참조하여, 세션에 저장된 멤버와 일치하는지 확인하고
            # 공모전 목록을 최신순으로 뽑아옴
            exhibitions = Exhibition.objects.filter(exhibitionmember__university=university).order_by('-id')

        # 학교회원인 경우에만 적용 (공모전 작성자는 학생회원만 가능)
        elif school:
            # 공모전 목록에서 Exhibition의 school_id와 세션에 저장된 멤버와 일치하는지 확인하고
            # 공모전 목록을 최신순으로 뽑아옴
            exhibitions = Exhibition.objects.filter(school=school).order_by('-id')

        # 일반회원인 경우 공모전이 없기때문에 None으로 선언 --> 일반회원으로 로그인시 공모전목록이 없는 에러를 해결할 수 있음
        else :
            exhibitions = None

        # 커뮤니티 목록 가져오기
        # status = 0 -> 게시 완료 인 커뮤니티 목록을 최신순으로 불러옴
        community = Community.objects.filter(member_id=member_id, status=0).order_by('-id')


        # 세션 정보 최신화
        request.session['member'] = MemberSerializer(Member.objects.get(id=request.session['member']['id'])).data
        check = request.GET.get('check')

        # 자료 공유 목록을 가져오는 로직
        # 자료 공유는 대학생만 가능하기 때문에, 우선 대학생인 회원의 아이디와 일치하는지 검증해서 첫번째 객체를 가져옴
        share_university = University.objects.filter(member_id=member_id).first()

        # 작성자가 공유한 목록
        # Share (자료공유)에 전에 선언한 share_university를 member_id에 검증하고 최신순으로 자료공유 목록을 불러옴
        share_write = Share.objects.filter(university=share_university).order_by('-id')

        # 구매자가 구매한 목록
        # 자료공유 구매자 -> ShareMember 모델에서 university와 share_university를 검증하고 자료공유 구매 목록을 최신순으로 불러옴
        share_pay = ShareMember.objects.filter(university=share_university).order_by('-id')

        # 페이지 번호 (화면에서 페이지처리로 불러오기 위해 page를 가져옴)
        page = request.GET.get('page', 1)

        # 페이지당 행 수
        # 자료공유 목록을 9개씩 불러옴
        share_row_count = 9

        # 필터링된 자료 공유 목록을 페이지별로 나눔 (Paginator 함수를 사용)
        share_paginator = Paginator(share_write if share_write else share_pay, share_row_count)

        # 예외처리 --> 페이지 처리를 할때 생기는 오류를 예방하기 위해서 사용함
        # shares --> 자료 공유 목록 페이지 처리 변수
        try:
            # 불러온 목록들을 페이지 처리함
            shares = share_paginator.page(page)
        except PageNotAnInteger:
            # 페이지 번호가 정수가 아닌 경우, 첫 페이지를 반환
            shares = share_paginator.page(1)
        except EmptyPage:
            # 페이지가 비어 있는 경우, 마지막 페이지를 반환
            shares = share_paginator.page(share_paginator.num_pages)

            # 파일 가져오기 (자료 공유 목록 페이지에서 파일을 추출해야 하기 때문에 for 문 사용)
            for p in shares:
                first_file = p.sharefile_set.first()
                if first_file:
                    file_name = first_file.path.name
                    # 파일 확장자 추출
                    file_extension = file_name.split('.')[-1].lower()
                    p.file_extension = file_extension
                    # 파일이 있으면 파일의 경로를 기반으로 URL 생성
                    p.image_url = f"{MEDIA_URL}{first_file.path}"
                else:
                    # 파일이 없는 경우에는 이미지 URL을 None으로 설정
                    p.image_url = None


        # 장소 공유 목록을 가져오는 로직
        # 학교회원 정보를 가져옴
        school = School.objects.filter(member_id=member_id).first()
        # 장소 공유 model 에서 school_id와 세션에 저장된 멤버가 일치하는지 확인 한 뒤
        # place_post_Status(게시 상태)가 1 or True인 (작성완료)인걸 최신순으로 불러온다.
        place = Place.objects.filter(school=school, place_post_status=1).order_by('-id')

        # 장소공유 목록의 page를 불러옴
        page = request.GET.get('page', 1)

        # 장소공유 목록을 초기화 시킨다.
        places = None

        # 로그인한 멤버가 대학생인 경우 (대학생 회원만 장소 공유 구매 가능 )
        if university:
            # 장소 공유 목록에서 기존 PlaceMember의 university_id를 역참조하여, 세션에 저장된 멤버와 일치하는지 확인하고
            # 장소공유 목록을 최신순으로 뽑아옴
            places = Place.objects.filter(placemember__university=university, place_order_status=1).order_by('-id')

        # 로그인한 멤버가 학교 회원인 경우 ( 학교 회원만 장소 공유 글 작성 가능 )
        elif school:
            # Place Model의 school_id와 school이 일치하는지 검증하고 최신순으로 불러옴
            places = Place.objects.filter(school=school, place_post_status=1).order_by('-id')


        # 페이지당 행 수
        # 장소 공유 목록을 9개씩 불러옴
        place_row_count = 9

        # 필터링된 장소 공유 목록을 페이지별로 나눔 (Paginator 함수를 사용)
        place_paginator = Paginator(place, place_row_count)

        # 현재 회원의 공유한 장소 공유 목록이 있으면
        if places:
            try:
                # 불러온 목록 들을 페이지 처리함
                places = place_paginator.page(page)
            except PageNotAnInteger:
                # 페이지 번호가 정수가 아닌 경우, 첫 페이지를 반환
                places = place_paginator.page(1)
            except EmptyPage:
                # 페이지가 비어 있는 경우, 마지막 페이지를 반환
                places = place_paginator.page(place_paginator.num_pages)
        else:
            # 현재 회원의 구매/공유한 장소 공유 목록이 없으면
            # place 를 None으로 설정하여 에러 방지
            places = None

        # 장소공유 목록 가져오기
        # 장소 공유 model 에서 school_id와 세션에 저장된 멤버가 일치하는지 확인 한 뒤
        # place_post_Status(게시 상태)가 1 or True인 (작성완료)인걸 최신순으로 불러온다.
        place1 = PlaceMember.objects.filter(place_member_status=0, university=university).order_by('-id')

        # 커뮤니티 목록 가져오기
        community = Community.objects.filter(member_id=member_id).order_by('-id')

        # 커뮤니티 페이징 처리
        page = request.GET.get('page', 1)
        # 커뮤니티 목록을 9개 불러옴
        community_row_count = 5
        # 불러온 목록을 페이지 처리함
        community_paginator = Paginator(community, community_row_count)
        try:
            # 불러온 목록 들을 페이지 처리함
            communities = community_paginator.page(page)

        except PageNotAnInteger:
            # 페이지가 비어 있는 경우, 마지막 페이지를 반환
            communities = community_paginator.page(1)
        except EmptyPage:
            # 페이지가 비어 있는 경우, 마지막 페이지를 반환
            communities = community_paginator.page(community_paginator.num_pages)

        # 기본 프로필 이미지 설정
        default_profile_url = 'https://static.wadiz.kr/assets/icon/profile-icon-1.png'
        # 세션의 멤버가 프로필이 없을때,
        if profile is None:
            # profile 설정
            profile = default_profile_url

        # 화면에 뿌려주기 위해 공통적으로 들어가는 context를 선언
        context = {
            'members': request.session['member'], # 멤버 정보
            'member_id': member_id, # 멤버 id
            'profile': profile, # 멤버 프로필
            'check': check, # 세션 정보 최신화
            'communities': communities, # 커뮤니티 정보
        }

        if highschool: # 고등학생 회원인 경우
            # CummunityFile 모델에서 community_id와 community.first()와 일치하하는지 확인하고 첫번째 객체를 가져옴
            context['community_file'] = CommunityFile.objects.filter(community_id=community.first()).first()
            # 고등학생 회원일 때 들어가지는 페이지에 context 정보를 추가해줌
            context['highschool'] = highschool

        if university: # 대학생  회원인 경우  아래 context를 대학생 회원일때 들어가지는 페이지에 추가한다.
            # 장소 공유 구매 목록를 불러온다.
            places = Place.objects.filter(placemember__university=university, placemember__place_member_status=0)
            context['community_file'] = CommunityFile.objects.filter(community_id=community.first()).first() # 커뮤니티 파일
            context['current_point'] = university.university_member_points # 잔여 포인트
            context['member_major'] = university.university_member_major # 회원 전공
            context['member_school'] = university.university_member_school # 회원의 학교
            context['places'] = places # 장소 정보
            context['place_file'] = PlaceFile.objects.filter(place_id=places.first()).first() # 장소 파일
            context['shares'] = shares # 자료 정보
            context['exhibitions'] = exhibitions # 공모전 정보

        if school: # 학교 회원인 경우
            member = request.session['member']['id'] # 멤버 아이디
            context['place_file'] = PlaceFile.objects.filter(place_id=place.first()).first() # 장소 대여 파일
            context['current_point'] = Point.objects.filter(member_id=member, point_status=3).aggregate(Sum('point'))['point__sum'] # 잔여 포인트
            context['places'] = places # 장소 정보
            context['school'] = school # 학교 회원 정보
            context['exhibitions'] = exhibitions # 공모전 정보

        else : # 일반회원인 경우
            context['community_file'] = CommunityFile.objects.filter(community_id=community.first()).first() # 커뮤니티 파일


        return render(request,
                      'mypage/main-high.html' if highschool else 'mypage/main-university.html' if university else 'mypage/main.html'
                      if school else 'mypage/main-nomal.html', context)


    # 프로필 기능 관련 View
    def post(self, request):
        data = request.POST
        file = request.FILES.get('profile')  # 'profile'은 input의 name 속성

        print('POST 들어옴')
        # 로그인 된 회원의 정보를 불러옴
        member = Member.objects.get(id=request.session['member']['id'])
        # 로그인 된 회원이 memberfile을 가져옴
        member_file = MemberFile.objects.filter(member=member).first()

        # 파일이 존재하는 경우에만 처리
        if file:
            # 회원에 저장된 파일이 없을때
            if member_file is None:
                # 파일 정보 추가
                file_instance = File.objects.create(file_size=file.size)
                # MemberFile 모델 정보 추가
                member_file = MemberFile.objects.create(member=member, file=file_instance, path=file)
            else:
                # 이미 존재하는 회원 파일의 경우 파일 사이즈를 업데이트하고 저장
                file_instance = member_file.file
                file_instance.file_size = file.size
                file_instance.save()
                member_file.path = file

            # 멤버 파일에 수정사항을 저장함
            member_file.save()

        # 현재 회원의 파일 목록을 조회하여 해당 파일들의 경로를 리스트로 가져와 세션에 있는 member_files 에 저장
        request.session['member_files'] = list(member.memberfile_set.values('path'))

        # 프로필 을 바꾸고 나서 myPage/main 으로 redirect!
        return redirect('myPage:main')

# 원랩 목록창 View
class MyPageOnelabAPI(APIView):
    def get(self, request):
        # 세션에 저장된 멤버의 id를 가져옴
        member_id = request.session['member']['id']
        # 랩장인지 랩원인지 구별 기능 / is-member == True (랩원)
        is_member = request.GET.get('is-member')
        # University에서 member_id가 위에 선언한 member_id와 일치하는 것중 첫번째 객체를 가져온다.
        university = University.objects.filter(member_id=member_id).first()

        # 대학생이 아닌 경우
        if not university:
            # 실패를 Response로 반환합니다.
            return Response("fail")

        onelabs = []
        if is_member == 'false':
            # 랩장인 경우
            # OneLab에서 해당 대학의 ID와 로그인한 회원의 대학 ID가 일치하는지 확인하고, 그 결과를 onelabs 변수에 저장
            onelabs = OneLab.objects.filter(university=university)
        else:
            # 랩원인 경우
            # OneLabMember 모델에서 해당 대학의 ID와 랩원 유형을 구별할 수 있는 onelab_member_status가 0 또는 1인 상태를 조회하고,
            # 그 결과에서 onelab_id 컬럼 값을 가져온다.
            onelab_ids = OneLabMember.objects.filter(university=university,
                                                     onelab_member_status__in=(0, 1)).values_list('onelab_id',
                                                                                                  flat=True)
            # 가져온 onelab_ids를 이용하여 OneLab에서 해당하는 랩원의 랩실(원랩) 정보를 가져옴.
            onelabs = OneLab.objects.filter(id__in=onelab_ids)

        # 데이터 준비
        data = []
        # 위에 선언한 onelabs(랩실 정보)에 아래와 같은 onelab_data를 data 라는 빈 리스트 변수에 담아준다.
        for onelab in onelabs:
            onelab_data = {
                'id': onelab.id, # 원랩 아이디
                'onelab_main_title': onelab.onelab_main_title, # 원랩 메인 제목
                'onelab_content': onelab.onelab_content, # 원랩 타이틀
                'onelab_detail_content': onelab.onelab_detail_content, # 원랩 상세 내용
                'onelab_url': onelab.onelab_url, # 원랩 url
                'onelab_max_count': onelab.onelab_max_count, # 원랩 최대 참가 인원
                'onelab_ask_email': onelab.onelab_ask_email, # 원랩 이메일
                'onelab_status': onelab.onelab_status, # 원랩 유형
                'onelab_post_status': onelab.onelab_post_status, # 원랩 자료 유형
                'university_id': onelab.university_id, # 대학생 pk(id)
                'path': None  # 기본값 설정
            }

            # OneLabFile 확인
            onelab_file = OneLabFile.objects.filter(onelab=onelab).first()
            # 원랩에 file이 있을 시에 path 경로 추가
            if onelab_file:
                onelab_data['path'] = onelab_file.path.url

            # OneLabBannerFile 확인 - 예시로 추가
            onelab_banner_file = OneLabFile.objects.filter(onelab=onelab).first()
            # 원랩 베너 파일 이 있을 시에 path 경로 추가
            if onelab_banner_file:
                onelab_data['banner_path'] = onelab_banner_file.path.url

            # onelab_data를 data 라는 빈 리스트 변수에 담아준다.
            data.append(onelab_data)


        return Response(data)


# 프로필 삭제 View
class DeleteProfileView(View):
    def post(self, request):
        # 기본 프로필 path 경로
        new_profile_path = 'member/2024/03/19/profile.jpg'
        # 로그인된 멤버의 pk
        member = request.session['member']['id']
        # 로그인된 멤버의 member_files --> 기본 프로필 path경로로 설정
        request.session['member_files'] = new_profile_path

        try:
            # 삭제시에는 기본 프로필 path로 바뀌게 설정
            profile = MemberFile.objects.filter(member_id=member).update(path=new_profile_path)
            # 프로필 삭제 정보 저장
            profile.save()

        except MemberFile.DoesNotExist:
            # 오류 발생 시 결과
            print('프로필이 존재하지 않습니다.')

        # 성공 시 결과
        return JsonResponse({'message': '프로필 이미지가 업데이트되었습니다.'})

# 마이 페이지 포인트 부분 View
class MyPagePointView(View):
    def get(self, request):
        # 로그인된 회원의 pk 가져옴
        member_id = request.session['member']['id']
        # 세션에 저장된 멤버가 대학생 회원일 때 첫번째 객체를 가져옴
        university = University.objects.filter(member_id=member_id).first()
        # 세션에 저장된 멤버가 학교 회원일 대 첫번째 객체를 가져옴
        school = School.objects.filter(member_id=member_id).first()

        try:
            # 충전한 포인트 내역 최신순
            charge_date = Point.objects.filter(member_id=member_id, point_status=1).order_by('-id')

            # 사용한 포인트 내역 최신순
            use_date = Point.objects.filter(member_id=member_id, point_status=2).order_by('-id')

            # 적립한 포인트 내역 최신순
            get_date = Point.objects.filter(member_id=member_id, point_status=3).order_by('-id')

            # 사용한 포인트 내역 중 첫번째 객체-> date
            use_datetime = use_date.first()
            # 충전한 포인트 내역 중 첫번째 객체-> dates
            charge_datetime = charge_date.first()
            # 적립한 포인트 내역 중 첫번째 객체-> datess
            get_datetime = get_date.first()



            if university:  # 대학생인 경우
                # 세션에 저장된 멤버의 pk를 가져온다.
                member = request.session['member']['id']
                # point_status -> 1:충전 , 2:사용 , 3:적립
                # 충전 포인트 : 포인트 모델에서 현재 멤버의 id와 point_status가 1인것을 조회하고 이 포인트들을 Sum 함수로 합산한다. 없으면 0
                get_points = Point.objects.filter(member_id=member, point_status=1).aggregate(Sum('point'))['point__sum'] or 0
                # 이렇게 사용할 수 도 있음 charge_date.aggregate(Sum('point'))['point__sum'] or 0

                # 사용 포인트 : 포인트 모델에서 이전에 선언한 사용한 포인트 내역으로 선언한 use_date 값들을 다 더한다. 없으면 0
                use_point = use_date.aggregate(Sum('point'))['point__sum'] or 0  # 사용한 포인트 합계
                # 이렇게 사용할 수 도 있음 use_point = Point.objects.filter(member_id=member , point_status = 2).aggregate(Sum('point'))['point__sum'] or 0

                # 적립 포인트 : 포인트 모델에서 멤버 id와 point_status가 3인 것을 조회하고 이 포인트들을 Sum 함수로 합산한다. 없으면 0
                point1 = Point.objects.filter(member_id=member, point_status=3).aggregate(Sum('point'))['point__sum'] or 0
                # 이렇게 사용할 수 도 있음 get_date.aggregate(Sum('point'))['point__sum'] or 0


                # 실제 잔여포인트 -> 대학생 모델에서 멤버를 가져오고, 그 멤버의 university_member_points 를 가져온다.
                # university_member_points의 자세한 설명과 기능은 Point의 views.py에 있습니다.
                real_point = University.objects.get(member_id=member).university_member_points

                # 템플릿에 들어갈 데이터
                context = {
                    'point1': point1, # 적립 포인트
                    'point': get_points, # 충전 포인트
                    'current_point': real_point, # 잔여 포인트
                    'use_point': use_point, # 사용 포인트
                    'charge_point': charge_date.aggregate(Sum('point'))['point__sum'] or 0,  # 충전한 포인트 합계
                    'use_time': use_datetime.updated_date if use_datetime else "없음",  # 최근 사용한 시간
                    'get_time': get_datetime.updated_date if get_datetime else '적립내역 없음', # 최근 적립한 시간
                    'charge_time': charge_datetime.updated_date if charge_datetime else '충전내역 없음',  # 최근 충전한 시간
                }
                return render(request, 'mypage/point.html', context)

            elif school:  # 학교 회원인 경우
                member = request.session['member']['id']
                # 학교 회원인 경우 적립 기능만 있기때문에 point_status가 3인것만 조회하여 합산하면 됨
                current_point1 = Point.objects.filter(member_id=member, point_status=3).aggregate(Sum('point'))['point__sum']
                context = {
                    'get_datetime' : get_datetime, # 최근 적립한 시간
                    'current_point1' : current_point1, # 적립 포인트 이자 잔여 포인트
                    'use_time' : get_datetime.updated_date if get_datetime else "적립내역 없음", # 최근 적립한 시간

                }
                return render(request,'mypage/school-point.html', context)
            else:
                # 처리할 수 있는 회원 타입이 아닌 경우(일반회원, 고등학생 회원 등등)
                raise ObjectDoesNotExist

        except ObjectDoesNotExist: # 객체가 존재하지 않을때, (데이터가 존재하지 않을 때)
            return redirect('myPage:main')

    # 마이페이지 메인화면의 포인트 버튼을 눌렀을 때 기능 구현 과정
    def post(self,request):
        # 세션에 저장된 멤버를 불러옴
        member_id = request.session['member']['id']
        # 현재 멤버의 포인트 정보를 불러옴
        point = Point.objects.filter(member_id=member_id)
        # PointSerializer를 사용하여 포인트 객체를 직렬화하고 데이터를 세션에 저장
        request.session['point'] = PointSerializer(point.first()).data
        # myPage:my_point 경로로 리다이렉션
        return redirect(request,'mypage:my_point')

# 로그아웃 기능 View -> 로그 아웃 버튼을 눌렀을 때 기능 구현
class MemberLogoutView(View):
    def get(self, request):
        # 현재 세션 정보 초기화
        request.session.clear()
        # 메인페이지로 리다이렉션
        return redirect('/')


class OneLabMembersAPI(View):
    def get(self, request):
        # 해당 University와 OneLab 정보 가져오기
        university = University.objects.get(member_id=request.session['member']['id'])
        # 원랩 모델에서 원랩을 생성한 대학생회원 인지를 조회.
        onelabs = OneLab.objects.filter(university=university)

        # onelab_info 라는 리스트 생성
        onelab_info = []
        # 원랩 내의 작성자들을 조회한다.
        for onelab in onelabs:
            # members_info 라는 리스트 생성
            members_info = []

            # 원랩 멤버에서 특정 원랩 아이디와 참가 상태인(1) 멤버를 조회
            # onelab에 해당하는 원랩 멤버들 중에 onelab_member_status가 1(참가 상태)인 멤버들을 가져온다
            # select_related 함수를 사용하여 관련된 university와 member 정보를 함께 조회한다.
            members = OneLabMember.objects.filter(onelab=onelab, onelab_member_status=1).select_related(
                'university__member')

            # 위에 선언한 ,members내의 정보를 추출한다.
            for member in members:
                member_info = {
                    'member_id': member.university.member.id, # 회원 아이디
                    'member_email': member.university.member.member_email, # 회원 이메일
                    'member_name': member.university.member.member_name, # 회원 이름
                    'member_major': member.university.university_member_major, # 회원 전공
                    'member_points': member.university.university_member_points, # 회원 잔여 포인트
                    'onelab_member_status': member.onelab_member_status # 원랩 회원 유형 (대기중, 참가, 거절, 탈퇴)
                }
                # 위에 선언한 members_info 리스트에 해당 context 정보를 추가
                members_info.append(member_info)
            # 위에 선언한 onelab_info 리스트에 members_info 리스트, 원랩의 아이디 정보를 추가
            onelab_info.append({
                'onelab_id': onelab.id,
                'members': members_info
            })

        return JsonResponse(onelab_info, safe=False)


# 랩장일때 랩원 탈퇴 시키는 기능 구현 함수
def delete_members(request):
    if request.method == 'POST': # POST 방식으로 요청할때
        data = json.loads(request.body) # fetch로 전송한 Json 정보를 요청받음
        selected_items = data.get("selected_items") # fetch에서 selected_items라는 데이터를 불러옴
        print(selected_items)
        print(selected_items)
        # 선택된 항목들의 상태를 3으로 변경하는 코드를 작성 --> 3이면 탈퇴로 바뀜
        for item_id in selected_items:
            try :
                OneLabMember.objects.filter(university__member__member_email=item_id).update(onelab_member_status=3)
                print('성공!')
            except :
                pass # 항목이 존재하지 않는 경우 무시

        return JsonResponse({'message': '선택된 회원이 성공적으로 탈퇴 되었습니다.'})
    return JsonResponse({'message': 'POST 요청이 필요합니다.'}, status=400)

# 랩원일때 탈퇴하기 기능 구현 함수
def delete_onelab(request):
    if request.method == 'POST': # POST 방식으로 요청할 때
        try:
            # fetch로 부터 전송받은 json 데이터를 utf-8 버전으로 디코딩하여 문자열로 변환함
            data = json.loads(request.body.decode('utf-8'))
            # fetch에서 요청받은 data인 selectedName을 불러옴 (selectedName : 원랩의 메인 타이틀)
            selected_item = data.get('selectedName')
            # 원랩에서 위에 선언한 selected_item를 조회함
            onelab = OneLab.objects.get(onelab_main_title=selected_item)
            # 세션에 저장된 멤버의 id
            member_id = request.session['member']['id']

            # 해당 사용자가 해당 OneLab에 속한 멤버인지 확인
            onelab_member = OneLabMember.objects.get(university_id=member_id, onelab_id=onelab.id)

            # 멤버 상태를 탈퇴(3)로 변경
            onelab_member.onelab_member_status = 3
            # 랩원 탈퇴 정보 저장
            onelab_member.save()

    # 결과 리턴 값
            return JsonResponse({'message': '선택된 항목이 성공적으로 탈퇴되었습니다.'})
        except ObjectDoesNotExist:
            return JsonResponse({'error': '해당 항목이 존재하지 않거나 권한이 없습니다.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST 요청이 필요합니다'}, status=400)

# 원랩 해체 하기 함수
def delete_all(request):
    if request.method == 'POST': # POST 방식으로 요청할 때
        # OneLab 모델에서 해당하는 객체 가져오기
        try:
            # fetch로 부터 전송받은 json 데이터를 utf-8 버전으로 디코딩하여 문자열로 변환함
            data = json.loads(request.body.decode('utf-8'))
            # fetch 내에 있는 data인 id를 가져옴
            onelabId = data.get('id')
            # 해당하는 원랩 객체 가져오기
            onelab = OneLab.objects.filter(id=onelabId).first()
            # 원랩이 존재할때
            if onelab:
                # onelab_post_status 값을 False로 변경
                onelab.onelab_post_status = False
                # 원랩 수정 정보 저장
                onelab.save()

                # 결과 리턴 반환
                return JsonResponse({'message': '원랩이 성공적으로 종료되었습니다.'})
            else:
                return JsonResponse({'message': '원랩을 찾을 수 없습니다.'}, status=404)

        except:
            return JsonResponse({'message': 'POST 요청이 필요합니다.'}, status=400)