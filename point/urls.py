from django.urls import path

from point.views import PointView, PointListView, PointListDetailView, PointUseListView, \
    PointUseDetailView, PointGetListView, PointGetDetailView

app_name = 'point'

urlpatterns = [
    path('new/', PointView.as_view(), name='new'),
    path('list/', PointListView.as_view(), name='list'),
    path('use/',PointUseListView.as_view(), name='use'),
    path('useDetail/',PointUseDetailView.as_view(), name='useDetail'),
    path('get/',PointGetListView.as_view(), name='get'),
    path('getDetail/',PointGetDetailView.as_view(), name='getDetail'),
    path('detail/', PointListDetailView.as_view(), name='detaillist')

]