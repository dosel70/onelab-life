import math
import ssl
from django.core.paginator import Paginator, EmptyPage
from community.models import Community
from django.utils import timezone
from exhibition.models import Exhibition
from django.db.models import Q, Sum
from member.models import MemberFile, Member
from member.serializers import MemberSerializer
from onelab.models import OneLab
from place.models import Place
from school.models import School
from rest_framework.views import APIView


from share.models import Share
from visitRecord.models import VisitRecord

ssl._create_default_https_context = ssl._create_unverified_context

from django.shortcuts import render, redirect
from django.views import View
from rest_framework.response import Response

class MainView(View):
    def get(self, request):
        places = Place.objects.all()
        place_info = {
            'places': []
        }
        # place 파일쪽
        for place in places:
            place_files = list(place.placefile_set.values('path'))
            place_info['places'].append({
                'files': place_files,
                'place_title': place.place_title,
                'place_address': place.school.school_member_address,
                'place_points': place.place_points,
                'place_date': place.place_date,
                'place_id': place.id,
                'school_name': place.school.school_name,
                'created_date': place.created_date,
            })

        # print(place_info)

        # 공모전쪽
        exhibitions = Exhibition.objects.all()
        exhibition_info = {
            'exhibitions': []
        }

        # 공모전 파일쪽
        for exhibition in exhibitions:
            exhibition_files = list(exhibition.exhibitionfile_set.values('path'))
            exhibition_info['exhibitions'].append({
                'files': exhibition_files,
                'exhibition_title': exhibition.exhibition_title,
                'exhibition_content': exhibition.exhibition_content,
                'exhibition_status': exhibition.exhibition_status,
            })
            print(exhibition_files)
        # print("들어옴")
        # print(exhibition_info)

        # 쉐어쪽
        shares = Share.objects.all()
        share_info = {
            'shares': []
        }

        # 쉐어 파일쪽
        for share in shares:
            share_files = list(share.sharefile_set.values('path'))
            share_info['shares'].append({
                'files': share_files,
                'id':share.id,
                'share_title': share.share_title,
                'share_content': share.share_content,
                'share_points': share.share_points,
                'share_choice_major': share.share_choice_grade,
                'share_type': share.share_type,
                'share_text_major': share.share_text_major,
                'share_text_name': share.share_text_name,
                'share_choice_grade': share.share_choice_grade,
            })

        # 원랩쪽
        onelabs = OneLab.objects.all()
        onelab_info = {
            'onelabs': []
        }

        # 원랩 파일쪽
        # for onelab in onelabs:
        #     onelab_files = list(onelab.onelabfile_set.values('path'))
        #     onelab_info['onelabs'].append({
        #         'files': onelab_files,
        #         'onelab_main_title': onelab.onelab_main_title,
        #         'onelab_content': onelab.onelab_content,
        #     })
        # print("들어옴")
        # print( onelab_info)
        #
        # # 커뮤니티 쪽
        # communities = Community.objects.all()
        # community_info = {
        #     'communities': []
        # }
        #
        # # 원랩 파일쪽
        # for community in communities:
        #     community.co
        #     community_files = list(community.)
        #     community_files = list(community.communityfile_set.values('path'))
        #     community_info['communities'].append({
        #         'files': community_files,
        #         'community_title': community.community_title,
        #         'community_content': community.community_content,
        #     })
        # print("들어옴")
        # print(onelab_info)
        # 방문자 기록
        visit_record, created = VisitRecord.objects.get_or_create(date=timezone.now().date())
        if created:
            visit_record.count = 1
        else:
            visit_record.count += 1
        visit_record.save()

        # 멤버쪽
        member_id = request.session.get('member', {}).get('id')
        default_profile_url = 'https://static.wadiz.kr/assets/icon/profile-icon-1.png'

        if member_id is None:
            profile = default_profile_url
            context = {
                'places': places,
                'exhibitions': exhibitions,
                'shares': shares,
                'onelabs': onelabs,
                'profile': profile,
            }
            return render(request, 'main/main-page.html', context)
        else:
            request.session['member_name'] = MemberSerializer(
                Member.objects.get(id=request.session['member']['id'])).data
            member = request.session['member']['id']
            profile = MemberFile.objects.filter(member_id=member).first()
            if profile is not None:
                context = {
                    'places': places,
                    'exhibitions': exhibitions,
                    'shares': shares,
                    'onelabs':onelabs,
                    'profile': profile,
                }
                return render(request, 'main/main-page.html', context)

        # Member.objects.create(**data)
            else:
                profile = default_profile_url
                context = {
                    'places': places,
                    'exhibitions': exhibitions,
                    'shares': shares,
                    'onelabs': onelabs,
                    'profile': profile,
                }
                return render(request, 'main/main-page.html', context)

            # Member.objects.create(**data)

        return render(request, 'main/main-page.html', {'places': places, 'exhibitions': exhibitions, 'shares': shares, 'onelabs':onelabs})
    #
    # def post(self, request):
    #     data = request.POST
    #     data = {
    #         'member_email': data['member-email'],
    #         'member_password': data['member-password'],
    #         'member_name': data['member-name'],
    #         'member_type': data['member-type'],
    #     }
    #
    #
    #

# class MainListAPI(APIView):
#
#     def get(self, request, page):
#         # 한 페이지에 보여줄 장소의 개수와 페이지당 표시할 최대 페이지 수 설정
#         row_count = 9
#
#         offset = (page - 1) * row_count
#         limit = page * row_count
#
#         # 공모전쪽
#         exhibitions = Exhibition.objects.all()
#         exhibition_info = {
#             'exhibitions': []
#         }
#
#         # 공모전 파일쪽
#         for exhibition in exhibitions:
#             exhibition_files = list(exhibition.exhibitionfile_set.values('path'))
#             exhibition_info['exhibitions'].append({
#                 'files': exhibition_files,
#                 'exhibition_title': exhibition.exhibition_title,
#                 'exhibition_content': exhibition.exhibition_content,
#                 'exhibition_status': exhibition.exhibition_status,
#             })
#
#         exhibition_count = exhibitions.count()
#
#         exhibition_info = {
#             'exhibitions': [],
#         }
#
#         has_next = exhibition_count > offset + limit
#
#         return Response(exhibition_info)