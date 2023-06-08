import datetime
from typing import List

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from in_app.api.serializer import PickUpScheduleSerializer
from in_app.models import PickUpSchedule


class PickUpScheduleManager:
    def __init__(self):
        self.today = datetime.datetime.now().date()

    @staticmethod
    def _make_schedule_unavailable(pick_up_schedule: PickUpSchedule) -> None:
        pick_up_schedule.available = False
        pick_up_schedule.save()

    @staticmethod
    def _make_schedule_completed(pick_up_schedule: PickUpSchedule) -> None:
        pick_up_schedule.schedule_completed = True
        pick_up_schedule.save()

    @staticmethod
    def _create_pick_up_schedule(date: datetime.date) -> None:
        start_times = [
            datetime.time(8, 0, 0),
            datetime.time(12, 0, 0),
            datetime.time(16, 0, 0)
        ]
        end_times = [
            datetime.time(11, 0, 0),
            datetime.time(15, 0, 0),
            datetime.time(19, 0, 0)
        ]
        for start_time, end_time in zip(start_times, end_times):
            PickUpSchedule.objects.create(
                start_time=start_time,
                end_time=end_time,
                available_quota=3,
                date=date
            )

    def create_or_get_pick_up_schedules(self) -> List[PickUpSchedule]:
        pick_up_schedules = PickUpSchedule.objects.all()
        last_date = self.today
        for pick_up_schedule in pick_up_schedules:
            last_date = pick_up_schedule.date
            if pick_up_schedule.date < self.today or (
                    pick_up_schedule.date == self.today and pick_up_schedule.end_time < datetime.datetime.now().time()):
                self._make_schedule_completed(pick_up_schedule)
                self._make_schedule_unavailable(pick_up_schedule)
        number_of_days = len(PickUpSchedule.objects.filter(schedule_completed=False))
        if number_of_days < 7:
            for i in range(7 - number_of_days):
                last_date += datetime.timedelta(days=1)
                self._create_pick_up_schedule(last_date)
        pick_up_schedules = PickUpSchedule.objects.filter(schedule_completed=False)
        for i in range(len(pick_up_schedules) - 7 * 3):
            last_object = pick_up_schedules.last()
            pick_up_schedules = pick_up_schedules.exclude(pk=last_object.pk)

        return pick_up_schedules


class CreateOrGetSchedulePickUpSlots(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        pick_up_schedule_manager = PickUpScheduleManager()
        pick_up_schedules = pick_up_schedule_manager.create_or_get_pick_up_schedules()
        serializer = PickUpScheduleSerializer(pick_up_schedules, many=True)
        return Response(serializer.data)


class GetPickUpSlotOnDay(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        try:
            date = datetime.datetime.strptime(pk, '%Y-%m-%d').date()
            pick_up_slots = PickUpSchedule.objects.filter(date=date)
        except ValueError:
            return Response({'error': 'Invalid date format. Please use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        except PickUpSchedule.DoesNotExist:
            return Response({'error': 'No pick-up slots found for this date.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PickUpScheduleSerializer(pick_up_slots, many=True)
        return Response(serializer.data)
